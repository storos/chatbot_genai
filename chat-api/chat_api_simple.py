import os
import sys
import re
import json
import psycopg
import requests
from psycopg.types.json import Json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import ChatOpenAI

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

# ==============================
# FastAPI App
# ==============================
app = FastAPI(title="Chat API with Memory & Tool Calling")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

def save_action(session_id: str, action_name: str, args: dict, result: str):
    ensure_session(session_id)
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chat_actions (session_id, action_name, args, result) VALUES (%s, %s, %s, %s)",
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
    return ("sipariş numaranız" in txt or "sipariş numarasını" in txt) and ("iptal nedenini" in txt or "sebep" in txt)

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
    order_number = None
    reason = None

    # ORD-12345 formatı veya sadece rakam
    m_num = re.search(r"(ORD[-]?\d+|\b\d{3,}\b)", message, re.IGNORECASE)
    if m_num:
        order_number = m_num.group()

    # Sebep patterns
    m_reason = re.search(r"sebep[:\-]?\s*(.*)", message, re.IGNORECASE)
    if m_reason:
        reason = m_reason.group(1).strip()
    else:
        # Diğer sebep ifadeleri
        m_alt = re.search(r"(hasarlı|bozuk|iade|yanlış|defolu|beğenmedim|uygun değil|fikrim değişti|fikir değiştirdim|istemiyorum|artık gerek yok)", message, re.IGNORECASE)
        if m_alt:
            reason = m_alt.group(1)

    return order_number, reason

# ==============================
# Health Check
# ==============================
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# ==============================
# Chat Endpoint
# ==============================
@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    ensure_session(req.session_id)
    save_message(req.session_id, "user", req.message)

    # ---- Tool Calling: Sipariş İptal İşlemi ----
    order_number, reason = extract_order_and_reason(req.message)
    
    # 1) Eğer önceki asistan iptal bilgilerini istemişse ve şimdi bilgiler geliyorsa → direkt iptal et
    if assistant_recently_asked_for_details(req.session_id) and order_number and reason:
        result = call_order_api(order_number, reason)
        save_action(req.session_id, "cancel_order", {"order_number": order_number, "reason": reason}, result)
        save_message(req.session_id, "assistant", result)
        return ChatResponse(answer=result, sources=[])
    
    # 2) Eğer önceki asistan iptal bilgilerini istemişse ve hala eksik bilgi varsa → tekrar sor
    if assistant_recently_asked_for_details(req.session_id):
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

    # ---- Basit Chat Yanıtı (RAG olmadan) ----
    history = get_session_history(req.session_id)
    context_messages = "\n".join([f"{h['role']}: {h['content']}" for h in history])

    # Basit bilgi bankası
    knowledge_base = """
    Müşteri Hizmetleri Bilgi Bankası:
    
    1. Sipariş Takibi:
    - Hesabım > Siparişlerim bölümünden takip edebilirsiniz
    - Kargo takibi için sipariş detayına giriniz
    
    2. İptal İşlemleri:
    - Sipariş iptal etmek için sipariş numaranız ve sebep belirtmeniz gerekir
    - İptal edilebilir siparişler: Henüz kargoya verilmemiş siparişler
    
    3. İade İşlemleri:
    - Hesabım > Siparişlerim > İade Et bölümünden yapabilirsiniz
    - İade süresi: Teslimat tarihinden itibaren 14 gün
    
    4. Teslimat Sorunları:
    - Teslimat gecikmesi için Müşteri Hizmetleri ile iletişime geçin
    - Hasarlı ürün teslimatı durumunda fotoğraf ile bildirim yapın
    """

    prompt = f"""
Sen bir müşteri destek asistanısın. Türkçe yanıt ver.

Geçmiş konuşma:
{context_messages}

Kullanıcının yeni mesajı:
{req.message}

Bilgi bankası:
{knowledge_base}

Cevabını sadece Türkçe ver ve yardımcı ol.
"""
    
    response = chat_model.invoke(prompt)
    answer = response.content if hasattr(response, "content") else str(response)

    # ---- İptal Niyeti Kontrolü ve Ek Teklif ----
    msg_lower = req.message.lower()
    cancel_intent = ("iptal" in msg_lower) or ("iade" in msg_lower)
    
    if cancel_intent:
        answer += "\n\nEğer isterseniz buradan sipariş numaranızı ve iptal nedeninizi paylaşırsanız, ben de iptal işleminizi gerçekleştirebilirim."
    
    save_message(req.session_id, "assistant", answer)
    return ChatResponse(answer=answer, sources=["knowledge_base"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)