-- Chatbot Database Schema - Ready to Execute
-- Copy this entire script and run in PgAdmin Query Tool

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;

-- Chat sessions
CREATE TABLE chat_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat messages  
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat actions (tool calls)
CREATE TABLE chat_actions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    action_name VARCHAR(255) NOT NULL,
    args JSONB NOT NULL,
    result TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LangChain collections
CREATE TABLE langchain_pg_collection (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    cmetadata JSON
);

-- LangChain embeddings
CREATE TABLE langchain_pg_embedding (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID REFERENCES langchain_pg_collection(uuid),
    embedding vector,
    document VARCHAR,
    cmetadata JSONB,
    custom_id VARCHAR
);

-- Performance indexes
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_actions_session_id ON chat_actions(session_id);

-- Default collection for chatbot docs
INSERT INTO langchain_pg_collection (name, cmetadata) 
VALUES ('chatbot_docs', '{"description": "Chatbot documentation collection"}');