from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
import os

def ingest_pdf():
    # PDF yükle - Docker container'da docs volume mount edilir
    # Hem Docker hem local çalışma için farklı path'leri dene
    pdf_paths = [
        "/docs/Chatbot_SSS.pdf",  # Docker volume mount path
        "../docs/Chatbot_SSS.pdf",  # Local relative path
        "docs/Chatbot_SSS.pdf"      # Alternative local path
    ]
    
    pdf_path = None
    for path in pdf_paths:
        if os.path.exists(path):
            pdf_path = path
            break
    
    if not pdf_path:
        raise FileNotFoundError("Chatbot_SSS.pdf not found in any of the expected locations")
    
    print(f"Loading PDF from: {pdf_path}")
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    # Chunk'lara ayır
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    docs = text_splitter.split_documents(docs)

    # Metadata ekle
    for i, d in enumerate(docs):
        d.metadata["source"] = "Chatbot_SSS.pdf"
        d.metadata["chunk"] = i

    embeddings = OpenAIEmbeddings()

    CONNECTION_STRING = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/chatbot"
    )

    # Yeni collection'a kaydet
    PGVector.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name="chatbot_docs",
        connection=CONNECTION_STRING,
        use_jsonb=True,  # metadata için JSONB kullan
    )

    print(f"{len(docs)} chunk PostgreSQL'e kaydedildi.")

if __name__ == "__main__":
    ingest_pdf()