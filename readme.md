# AI-Powered Customer Support Chatbot

A sophisticated customer support chatbot system that combines natural language processing with automated order management capabilities. Built with modern AI technologies to provide intelligent customer service.

## 🚀 Key Features

### 🤖 Intelligent Conversation Management
- **Session-based Chat**: Persistent conversation history for each user session
- **Context Awareness**: Maintains conversation context across multiple interactions
- **Natural Language Understanding**: Processes customer queries in Turkish with high accuracy

### 📚 Knowledge Base Integration (RAG)
- **Document Retrieval**: Searches through company documentation using vector embeddings
- **Semantic Search**: Finds relevant information based on meaning, not just keywords
- **Source Attribution**: Provides references to source documents for transparency

### 🛒 Automated Order Management
- **Smart Order Cancellation**: Automatically processes order cancellation requests
- **Information Extraction**: Intelligently extracts order numbers and cancellation reasons from natural language
- **Multi-step Process**: Guides customers through cancellation process with missing information collection
- **API Integration**: Seamlessly integrates with order management systems

### 💬 Enhanced Customer Experience
- **Hybrid Responses**: Combines knowledge base information with actionable order management
- **Proactive Assistance**: Offers order cancellation services when cancellation intent is detected
- **Graceful Degradation**: Falls back to general support when specific actions aren't applicable

## 🛠️ Tech Stack

### Backend Framework
- **FastAPI**: Modern, fast web framework for building APIs with Python
- **Pydantic**: Data validation and serialization using Python type annotations

### AI & Machine Learning
- **OpenAI GPT-4o-mini**: Advanced language model for natural language understanding and generation
- **LangChain**: Framework for developing applications with large language models
- **OpenAI Embeddings**: Vector embeddings for semantic search capabilities

### Database & Storage
- **PostgreSQL**: Robust relational database for structured data storage
- **PGVector**: PostgreSQL extension for vector similarity search
- **psycopg**: Modern PostgreSQL adapter for Python

### Deployment & Infrastructure
- **Docker**: Containerization for easy deployment and scalability
- **Docker Compose**: Multi-container application orchestration

### Additional Libraries
- **Requests**: HTTP library for API integrations
- **Regular Expressions**: Pattern matching for information extraction

## 🐳 Docker Setup & Deployment

### Prerequisites
- Docker and Docker Compose installed
- OpenAI API key

### Environment Variables
Create a `.env` file in the root directory:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Full System Deployment
Start all services with Docker Compose:
```bash
# Start all services (PostgreSQL + PgAdmin + Chat API + Order API)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Individual Service Deployment

#### 1. Order API Only
```bash
# Build and run Order API
docker build -t chatbot-order-api ./order-api
docker run -d --name order-api -p 9000:9000 chatbot-order-api

# Test Order API
curl -X POST "http://localhost:9000/cancel" \
  -H "Content-Type: application/json" \
  -d '{"order_number": "ORD-12345", "reason": "Changed mind"}'
```

#### 2. Chat API Only (requires database)
```bash
# Note: PostgreSQL database must be running first (see "Database Only" section below)

# Build and run Chat API
docker build -t chatbot-chat-api ./chat-api
docker run -d --name chat-api \
  -p 8001:8001 \
  -e OPENAI_API_KEY="your_openai_api_key_here" \
  -e DATABASE_URL="postgresql://postgres:postgres@host.docker.internal:5432/chatbot" \
  -e ORDER_API_URL="http://host.docker.internal:9000/cancel" \
  chatbot-chat-api

# Test Chat API
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test123", "message": "Merhaba, nasılsınız?"}'
```

#### 3. Database Only
```bash
# PostgreSQL with PGVector
docker run -d --name chatbot-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=chatbot \
  -p 5432:5432 \
  -v chatbot_db_data:/var/lib/postgresql/data \
  pgvector/pgvector:pg16

# PgAdmin (optional)
docker run -d --name chatbot-pgadmin \
  -e PGADMIN_DEFAULT_EMAIL=admin@admin.com \
  -e PGADMIN_DEFAULT_PASSWORD=admin \
  -p 5050:80 \
  dpage/pgadmin4
```

#### 4. Ingest Script (Database Initialization)
```bash
# Build ingest image
docker build -t chatbot-ingest ./ingest

# Run ingest script (one-time execution)
docker run --rm \
  -e OPENAI_API_KEY="your_openai_api_key_here" \
  -e DATABASE_URL="postgresql+psycopg://postgres:postgres@host.docker.internal:5432/chatbot" \
  -v "$(pwd)/docs:/docs" \
  chatbot-ingest

# Note: This container runs once and exits after completing the data ingestion
```

### Service URLs
- **Chat API**: http://localhost:8001
- **Order API**: http://localhost:9000  
- **PostgreSQL**: localhost:5432
- **PgAdmin**: http://localhost:5050

### Database Setup & Initialization

After starting PostgreSQL, you **must** initialize the database schema and load the knowledge base:

#### 1. Create Database Schema
```bash
# First, create required tables using the initialization script
cd database
psql -h localhost -p 5432 -U postgres -d chatbot -f init_schema.sql

# Or if you have PostgreSQL client installed via Docker:
docker exec -i chatbot_db psql -U postgres -d chatbot < database/init_schema.sql
```

#### 2. Load Knowledge Base (PDF Documents)

**Option A: Using Docker (Recommended)**
```bash
# Build ingest container
docker build -t chatbot-ingest ./ingest

# Run ingest script with volume mount for PDF access
docker run --rm \
  -e OPENAI_API_KEY="your_openai_api_key_here" \
  -e DATABASE_URL="postgresql+psycopg://postgres:postgres@host.docker.internal:5432/chatbot" \
  -v "$(pwd)/docs:/docs" \
  chatbot-ingest
```

**Option B: Using Python directly**
```bash
# Set environment variables for ingest script
export OPENAI_API_KEY="your_openai_api_key_here"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/chatbot"

# Run ingest script to load PDF data into vector database
cd ingest
python3 ingest.py
```

#### 3. Verify Database Setup
```bash
# Connect to database and verify tables
psql -h localhost -p 5432 -U postgres -d chatbot

# Check if tables are created
\dt

# Check if vector data is loaded
SELECT COUNT(*) FROM langchain_pg_embedding;
```

**⚠️ Important**: The Chat API **requires** both the database schema and PDF data to be loaded for full functionality including RAG (Retrieval Augmented Generation).

## 📋 Installation & Setup

### Prerequisites
- Python 3.8+
- Docker & Docker Compose
- OpenAI API Key

### 1. Start Database Services
```bash
docker compose up -d
```

### 2. Load Knowledge Base
```bash
python3 ingest.py
```

### 3. Start Order API Service
```bash
python3 -m uvicorn order_api:app --reload --port 9000
```

### 4. Start Chat API Service
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/chatbot"
export ORDER_API_URL="http://localhost:9000/cancel"
python3 -m uvicorn chat_api:app --reload --port 8001
```

## 🔗 API Usage

### Chat Endpoint
**URL:** `http://127.0.0.1:8001/chat`
**Method:** POST

**Sample Request:**
```json
{
  "session_id": "user1", 
  "message": "I want to cancel my order 12345 because the product is damaged"
}
```

**Sample Response:**
```json
{
  "answer": "I understand you want to cancel your order. Based on our cancellation policy... ✅ Order 12345 has been successfully cancelled. Reason: product is damaged",
  "sources": ["policy.pdf - chunk 1", "faq.pdf - chunk 3"]
}
```

## 🏗️ Architecture

```
User Request → Chat API → {
  ├── RAG System (Knowledge Base Search)
  ├── Order Processing (Smart Extraction & API Calls)
  ├── Session Management (Database)
  └── Response Generation (AI + Context)
}
```

## 🎯 Use Cases

- **E-commerce Customer Support**: Handle product inquiries, order status, and cancellations
- **Help Desk Automation**: Provide instant responses to common questions
- **Order Management**: Streamline order modification and cancellation processes
- **Knowledge Base Query**: Quick access to company policies and procedures

## 🔧 Customization

The system is designed to be easily customizable:
- **Knowledge Base**: Add your own documents to the `docs/` folder
- **Order API**: Modify `order_api.py` to integrate with your order management system
- **Language Support**: Adjust prompts and regex patterns for different languages
- **AI Model**: Configure different OpenAI models based on your needs

## 📊 Monitoring & Analytics

- **Session Tracking**: All conversations are logged with session IDs
- **Action Logging**: Order cancellations and other actions are tracked
- **Source Attribution**: Track which documents are most helpful

---

*Built with ❤️ using modern AI technologies for enhanced customer experience*
