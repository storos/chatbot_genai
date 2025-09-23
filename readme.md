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
- **Database-dependent**: Returns clear error messages when data is unavailable, ensuring transparency

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

## � Installation & Setup

### Prerequisites
- Docker and Docker Compose installed
- OpenAI API key
- Python 3.8+ (for local development)

### Environment Variables
Create a `.env` file in the root directory:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

## 🐳 Docker Deployment (Recommended)

### Option 1: Full System with Docker Compose
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

### Option 2: Individual Service Deployment

#### 1. Database Setup
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
  -e PGLADMIN_DEFAULT_EMAIL=admin@admin.com \
  -e PGADMIN_DEFAULT_PASSWORD=admin \
  -p 5050:80 \
  dpage/pgadmin4
```

#### 2. Initialize Database Schema
```bash
# Create required tables using the initialization script
docker exec -i chatbot_db psql -U postgres -d chatbot < database/init_schema.sql
```

#### 3. Load Knowledge Base (PDF Documents)
```bash
# Build ingest container
docker build -t chatbot-ingest ./ingest

# Run ingest script (one-time execution)
docker run --rm \
  -e OPENAI_API_KEY="your_openai_api_key_here" \
  -e DATABASE_URL="postgresql+psycopg://postgres:postgres@host.docker.internal:5432/chatbot" \
  -v "$(pwd)/docs:/docs" \
  chatbot-ingest
```

#### 4. Order API
```bash
# Build and run Order API
docker build -t chatbot-order-api ./order-api
docker run -d --name chatbot-order-api -p 9000:9000 chatbot-order-api

# Test Order API
curl -X POST "http://localhost:9000/cancel" \
  -H "Content-Type: application/json" \
  -d '{"order_number": "ORD-12345", "reason": "Changed mind"}'
```

#### 5. Chat API
```bash
# Build and run Chat API
docker build -t chatbot-chat-api ./chat-api
docker run -d --name chatbot-chat-api \
  -p 8001:8001 \
  --network chatbot_genai_default \
  -e OPENAI_API_KEY="your_openai_api_key_here" \
  -e DATABASE_URL="postgresql://postgres:postgres@chatbot_db:5432/chatbot" \
  -e ORDER_API_URL="http://chatbot-order-api:9000/cancel" \
  chatbot-chat-api

# Test Chat API
curl -X POST "http://localhost:8001/chat" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test123", "message": "Merhaba, nasılsınız?"}'
```

### Service URLs
- **Chat API**: http://localhost:8001
- **Order API**: http://localhost:9000  
- **PostgreSQL**: localhost:5432
- **PgAdmin**: http://localhost:5050

**⚠️ Important**: The Chat API **requires** both the database schema and PDF data to be loaded for full functionality including RAG (Retrieval Augmented Generation).

## 🔗 API Usage

### Chat Endpoint
**URL:** `http://localhost:8001/chat`
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
  "sources": ["Chatbot_SSS.pdf - chunk 1", "Chatbot_SSS.pdf - chunk 3"]
}
```

### Health Check
```bash
# Check Chat API health
curl http://localhost:8001/health

# Check Order API  
curl -X POST http://localhost:9000/cancel \
  -H "Content-Type: application/json" \
  -d '{"order_number": "test", "reason": "test"}'
```

## 🏗️ Architecture

```
User Request → Chat API → {
  ├── RAG System (Knowledge Base Search via PGVector)
  ├── Order Processing (Smart Extraction & API Calls)
  ├── Session Management (PostgreSQL Database)
  └── Response Generation (OpenAI GPT-4o-mini + Context)
}
```

## 🎯 Use Cases

- **E-commerce Customer Support**: Handle product inquiries, order status, and cancellations
- **Help Desk Automation**: Provide instant responses to common questions
- **Order Management**: Streamline order modification and cancellation processes
- **Knowledge Base Query**: Quick access to company policies and procedures

## 🔧 Customization

The system is designed to be easily customizable:
- **Knowledge Base**: Add your own documents to the `docs/` folder and run ingest
- **Order API**: Modify `order_api.py` to integrate with your order management system
- **Language Support**: Adjust prompts and regex patterns for different languages
- **AI Model**: Configure different OpenAI models based on your needs

## 📊 Monitoring & Analytics

- **Session Tracking**: All conversations are logged with session IDs
- **Action Logging**: Order cancellations and other actions are tracked
- **Source Attribution**: Track which documents are most helpful
- **Error Handling**: Clear error messages when database or vector data is unavailable

## 🚀 Production Deployment

For production deployment:
1. Use environment variables for all sensitive data
2. Set up proper database backups
3. Configure monitoring and logging
4. Use Docker secrets for API keys
5. Set up SSL/TLS for external access
6. Consider horizontal scaling with load balancers

---

*Built with ❤️ using modern AI technologies for enhanced customer experience*
