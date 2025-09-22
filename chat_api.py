import os
import sys
import re
import json
import psycopg
import requests
from psycopg.types.json import Json
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_postgres import PGVector

# ==============================
# Environment Checks
# ==============================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
ORDER_API_URL = os.getenv("ORDER_API_URL")

missing = []
if not OPENAI_API_KEY: missing.append("OPENAI_API_KEY")
if not DATABASE_URL:   missing.append("DATABASE_URL")
if not ORDER_API_URL:  missing.append("ORDER_API_URL")
if missing:
    print(f"❌ ERROR: Missing environment variables: {', '.join(missing)}")
    sys.exit(1)

# ==============================
# Database Connection
# ==============================
try:
    conn = psycopg.connect(DATABASE_URL)
    conn.autocommit = True
except Exception as e:
    print(f"❌ ERROR: Could not connect to database: {e}")
    sys.exit(1)

# ==============================
# LangChain Setup
# ==============================
chat_model = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=OPENAI_API_KEY)
embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
vectorstore = PGVector(
    connection=DATABASE_URL,
    embeddings=embeddings,
    collection_name="chatbot_docs",
    use_jsonb=True,
)

# ==============================
# FastAPI App
# ==============================
app = FastAPI(title="Chat API with Memory & Tool Calling")

# ==============================
# Schemas
# ==============================
class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[str]

# ==============================
# Helper DB Functions
# ==============================
def ensure_session(session_id: str):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chat_sessions (session_id) VALUES (%s) ON CONFLICT DO NOTHING",
            (session_id,),
        )

def save_message(session_id: str, role: str, content: str):
    ensure_session(session_id)
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chat_messages (session_id, role, content) VALUES (%s, %s, %s)",
            (session_id, role, content),
        )

_ACTION_COL_CACHE = None
def _detect_action_column() -> str:
    global _ACTION_COL_CACHE
    if _ACTION_COL_CACHE:
        return _ACTION_COL_CACHE
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'chat_actions'
        """)
        cols = {r[0] for r in cur.fetchall()}
    # tercih sırası
    for name in ("action_name", "action", "tool_name"):
        if name in cols:
            _ACTION_COL_CACHE = name
            return name
    # hiçbiri yoksa varsayılan
    _ACTION_COL_CACHE = "action_name"
    return _ACTION_COL_CACHE

def save_action(session_id: str, action_name: str, args: dict, result: str):
    ensure_session(session_id)
    col = _detect_action_column()
    with conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO chat_actions (session_id, {col}, args, result) VALUES (%s, %s, %s, %s)",
            (session_id, action_name, Json(args), result),
        )

def get_session_history(session_id: str):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT role, content FROM chat_messages WHERE session_id = %s ORDER BY created_at ASC",
            (session_id,),
        )
        rows = cur.fetchall()
    return [{"role": r, "content": c} for r, c in rows]

def assistant_recently_asked_for_details(session_id: str) -> bool:
    """Son asistan mesajı sipariş no + sebep istiyor mu? Basit heuristik."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT content FROM chat_messages
            WHERE session_id = %s AND role = 'assistant'
            ORDER BY created_at DESC LIMIT 1
            """,
            (session_id,),
        )
        row = cur.fetchone()
    if not row:
        return False
    txt = row[0].lower()
    return ("sipariş numaranız" in txt or "sipariş numarasını" in txt) and ("sebep" in txt)

# ==============================
# Tool: Call Order API
# ==============================
def call_order_api(order_number: str, reason: str) -> str:
    try:
        resp = requests.post(
            ORDER_API_URL,
            json={"order_number": order_number, "reason": reason},
            timeout=8,
        )
        if resp.status_code == 204:
            return f"✅ Sipariş {order_number} başarıyla iptal edildi. Sebep: {reason}"
        return f"❌ Sipariş iptal edilemedi. Status: {resp.status_code}, Response: {resp.text}"
    except Exception as e:
        return f"❌ Sipariş iptalinde hata: {str(e)}"

# ==============================
# Parsing helpers
# ==============================
def extract_order_and_reason(message: str):
    """
    - order_number: ilk 3+ basamaklı sayı
    - reason: 'sebep' sözcüğünden sonrası (':' veya '-' opsiyonel)
    """
    order_number = None
    reason = None

    m_num = re.search(r"\b\d{3,}\b", message)
    if m_num:
        order_number = m_num.group()

    m_reason = re.search(r"sebep[:\-]?\s*(.*)", message, re.IGNORECASE)
    if m_reason:
        reason = m_reason.group(1).strip()

    # reason yoksa bazı kısa varyantlar
    if not reason:
        # ör: “ürün hasarlı”, “ürün bozuk” gibi tek cümlelik mesajlar
        m_alt = re.search(r"(hasarlı|bozuk|iade|yanlış|defolu|beğenmedim|uygun değil)", message, re.IGNORECASE)
        if m_alt:
            reason = m_alt.group(1)

    return order_number, reason

# ==============================
# Chat Endpoint
# ==============================
@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    ensure_session(req.session_id)
    save_message(req.session_id, "user", req.message)

    # ---- Tool Calling ÖNCELİKLE ----
    # 1) Eğer mesajdan hem sipariş no hem sebep çıkıyorsa → direkt order_api çağır.
    order_number, reason = extract_order_and_reason(req.message)
    if order_number and reason:
        result = call_order_api(order_number, reason)
        save_action(req.session_id, "cancel_order", {"order_number": order_number, "reason": reason}, result)
        save_message(req.session_id, "assistant", result)
        return ChatResponse(answer=result, sources=[])

    # 2) Eğer bu mesajda iptal niyeti varsa veya önceki asistan bu bilgileri istemişse → eksik alanı sor.
    msg_lower = req.message.lower()
    cancel_intent = ("iptal" in msg_lower) or ("iade" in msg_lower) or assistant_recently_asked_for_details(req.session_id)
    if cancel_intent:
        missing = []
        if not order_number:
            missing.append("sipariş numarası")
        if not reason:
            missing.append("sebep")
        if missing:
            ask = " ve ".join(missing)
            answer = f"İptal işlemi için {ask} bilgisini paylaşır mısınız?"
            save_message(req.session_id, "assistant", answer)
            return ChatResponse(answer=answer, sources=[])

    # ---- Normal RAG Akışı ----
    history = get_session_history(req.session_id)
    context_messages = "\n".join([f"{h['role']}: {h['content']}" for h in history])

    results = vectorstore.similarity_search(req.message, k=4)
    docs_text = "\n".join([r.page_content for r in results])
    sources = [f"{r.metadata.get('source')} - chunk {r.metadata.get('chunk')}" for r in results]

    prompt = f"""
Sen bir müşteri destek asistanısın.

Geçmiş konuşma:
{context_messages}

Kullanıcının yeni mesajı:
{req.message}

İlgili dökümanlardan bilgiler:
{docs_text}

Cevabını sadece Türkçe ver.
"""
    response = chat_model.invoke(prompt)
    answer = response.content if hasattr(response, "content") else str(response)

    save_message(req.session_id, "assistant", answer)
    return ChatResponse(answer=answer, sources=sources)