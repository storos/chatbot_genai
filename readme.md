Installation
1. Prepare PostgreSQL and PGVector with using "docker compose up -d"
2. Load FAQ document with using ingest script with command "python3 ingest.py"
3. Run order api with command "python3 -m uvicorn order_api:app --reload --port 9000"
4. Run chat api with command below
OPENAI_API_KEY="sk-***"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/chatbot"
export ORDER_API_URL="http://localhost:9000/cancel"
python3 -m uvicorn chat_api:app --reload --port 8001

You can start chatting with bot on endpoint http://127.0.0.1:8001/chat
sample payload is 
{ "session_id": "user1", "message": "hello, where is my order with number 12345" }
