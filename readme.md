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
