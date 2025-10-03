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
    tool_calls: list[dict] = []  # Tool calling bilgileri

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
    """Son asistan mesajı sipariş iptal detayları istiyor mu?"""
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
        print("DEBUG: No assistant message found")
        return False
    txt = row[0].lower()
    print(f"DEBUG: Last assistant message: '{txt[:100]}...'")
    
    # Eğer son mesaj başarılı iptal mesajıysa, artık detay isteme modunda değiliz
    if "başarıyla iptal edildi" in txt or "✅" in txt:
        print("DEBUG: Last message was successful cancellation, not asking for details anymore")
        return False
    
    has_order = ("sipariş numaranız" in txt or "sipariş numarasını" in txt or "sipariş" in txt)
    has_reason = ("iptal nedenini" in txt or "sebep" in txt or "nedeni" in txt)
    has_iptal = ("iptal işlemi" in txt or "işlemi" in txt or "iptal" in txt)
    print(f"DEBUG: has_order={has_order}, has_reason={has_reason}, has_iptal={has_iptal}")
    result = (has_order or has_reason) and has_iptal
    print(f"DEBUG: Final result: {result}")
    return result

# ==============================
# Tool: Call Order API
# ==============================
def call_order_api(order_number: str, reason: str) -> tuple[str, dict]:
    """Order API'yi çağır ve sonuç + detayları döndür"""
    tool_info = {
        "tool_name": "cancel_order",
        "endpoint": f"{ORDER_API_URL}/cancel",
        "method": "POST",
        "request_data": {"order_number": order_number, "reason": reason},
        "response_status": None,
        "response_data": None,
        "error": None
    }
    
    try:
        resp = requests.post(
            f"{ORDER_API_URL}/cancel",
            json={"order_number": order_number, "reason": reason},
            timeout=8,
        )
        tool_info["response_status"] = resp.status_code
        
        if resp.status_code == 204:
            tool_info["response_data"] = "Order cancelled successfully"
            result = f"✅ Sipariş {order_number} başarıyla iptal edildi. Sebep: {reason}"
        else:
            tool_info["response_data"] = resp.text
            result = f"❌ Sipariş iptal edilemedi. Status: {resp.status_code}, Response: {resp.text}"
            
    except Exception as e:
        tool_info["error"] = str(e)
        result = f"❌ Sipariş iptalinde hata: {str(e)}"
    
    return result, tool_info

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
        # Diğer sebep ifadeleri - eğer mesaj sadece sebep kelimesi ise, tümünü sebep olarak al
        m_alt = re.search(r"(hasarlı|bozuk|iade|yanlış|defolu|beğenmedim|uygun değil|fikrim değişti|fikir değiştirdim|istemiyorum|artık gerek yok|kalitesiz|kötü|iyi değil)", message, re.IGNORECASE)
        if m_alt:
            reason = m_alt.group(1)
        elif (len(message.strip().split()) <= 3 and 
              not re.match(r'^\d+$', message.strip()) and
              not any(word in message.lower() for word in ['sipariş', 'numara', 'order', 'number'])):  # Sipariş numarası ifadelerini hariç tut
            reason = message.strip()

    return order_number, reason

def get_session_context_for_order(session_id: str):
    """Session'daki tüm user mesajlarından order_number ve reason bilgilerini topla"""
    order_number = None
    reason = None
    
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT content FROM chat_messages
            WHERE session_id = %s AND role = 'user'
            ORDER BY created_at DESC LIMIT 10
            """,
            (session_id,),
        )
        rows = cur.fetchall()
    
    # En son mesajlardan order_number ve reason ara
    for row in rows:
        content = row[0]
        msg_order, msg_reason = extract_order_and_reason(content)
        
        if msg_order and not order_number:
            order_number = msg_order
        # Reason geçerli mi kontrol et (sadece rakam olmamalı, iptal/selamlama kelimeleri içermemeli)
        if (msg_reason and not reason and 
            not re.match(r'^\d+$', msg_reason.strip()) and 
            not any(word in msg_reason.lower() for word in ['iptal', 'merhaba', 'selam', 'hello', 'hi', 'iyi günler', 'günaydın'])):
            reason = msg_reason
            
        # Her ikisi de bulunduysa dur
        if order_number and reason:
            break
    
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
    print(f"DEBUG: Current message - order_number: {order_number}, reason: {reason}")
    
    # Eğer current mesajda eksik bilgi varsa, session context'ten tamamlamaya çalış
    if not order_number or not reason:
        context_order, context_reason = get_session_context_for_order(req.session_id)
        print(f"DEBUG: Session context - order_number: {context_order}, reason: {context_reason}")
        if not order_number:
            order_number = context_order
        if not reason:
            reason = context_reason
    
    print(f"DEBUG: Final - order_number: {order_number}, reason: {reason}")
    print(f"DEBUG: assistant_recently_asked_for_details: {assistant_recently_asked_for_details(req.session_id)}")
    
    # 1) Eğer önceki asistan iptal bilgilerini istemişse ve şimdi bilgiler geliyorsa → direkt iptal et
    # Current reason MEVCUT mesajdan gelmeli, order number session'dan olabilir
    current_order, current_reason = extract_order_and_reason(req.message)
    final_order = current_order if current_order else order_number  # Session'dan da olabilir
    if (assistant_recently_asked_for_details(req.session_id) and 
        final_order and current_reason and 
        not re.match(r'^\d+$', current_reason.strip())):
        result, tool_info = call_order_api(final_order, current_reason)
        save_action(req.session_id, "cancel_order", {"order_number": final_order, "reason": current_reason}, result)
        save_message(req.session_id, "assistant", result)
        return ChatResponse(answer=result, sources=[], tool_calls=[tool_info])
    
    # 2) Eğer önceki asistan iptal bilgilerini istemişse ve hala eksik bilgi varsa → tekrar sor
    if assistant_recently_asked_for_details(req.session_id):
        missing = []
        final_order = current_order if current_order else order_number  # Session'dan da olabilir
        if not final_order:
            missing.append("sipariş numarası")
        if not current_reason:
            missing.append("sebep")
        if missing:
            ask = " ve ".join(missing)
            answer = f"İptal işlemi için {ask} bilgisini paylaşır mısınız?"
            save_message(req.session_id, "assistant", answer)
            return ChatResponse(answer=answer, sources=[], tool_calls=[])

    # ---- Vector Database RAG ----
    history = get_session_history(req.session_id)
    context_messages = "\n".join([f"{h['role']}: {h['content']}" for h in history])

    # Try vector search first, fallback to knowledge base
    try:
        # Initialize PGVector with proper parameters
        vectorstore = PGVector(
            embeddings=embeddings,
            connection=DATABASE_URL,
            collection_name="chatbot_docs",
            use_jsonb=True,
        )
        results = vectorstore.similarity_search(req.message, k=4)
        docs_text = "\n".join([r.page_content for r in results])
        sources = [f"{r.metadata.get('source', 'unknown')} - chunk {r.metadata.get('chunk', 'N/A')}" for r in results]
        
        if not docs_text.strip():
            # If no relevant docs found, return error message
            error_msg = "⚠️ Üzgünüm, şu anda sistem bilgi bankasında veri bulunmuyor. Lütfen daha sonra tekrar deneyin veya müşteri hizmetleri ile iletişime geçin."
            save_message(req.session_id, "assistant", error_msg)
            return ChatResponse(answer=error_msg, sources=[], tool_calls=[])
            
    except Exception as e:
        print(f"Vector search error: {e}")
        # Return error message for database issues
        error_msg = "⚠️ Üzgünüm, şu anda sistem veritabanına erişimde sorun yaşanıyor. Lütfen daha sonra tekrar deneyin veya müşteri hizmetleri ile iletişime geçin."
        save_message(req.session_id, "assistant", error_msg)
        return ChatResponse(answer=error_msg, sources=[], tool_calls=[])

    prompt = f"""
Sen bir müşteri destek asistanısın. Türkçe yanıt ver.

Geçmiş konuşma:
{context_messages}

Kullanıcının yeni mesajı:
{req.message}

İlgili dökümanlardan bilgiler:
{docs_text}

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
    return ChatResponse(answer=answer, sources=sources, tool_calls=[])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)