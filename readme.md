-- docs loader
python3 ingest.py

-- order api
python3 -m uvicorn order_api:app --reload --port 9000

-- chat api
export OPENAI_API_KEY="sk-***"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/chatbot"
export ORDER_API_URL="http://localhost:9000/cancel"
python3 -m uvicorn chat_api:app --reload --port 8001