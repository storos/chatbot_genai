from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
import os

def ingest_pdf():
    # PDF yükle - Docker container'da docs volume mount edilir
    # Hem Docker hem local çalışma için farklı path'leri dene
    pdf_paths = [
        "/app/docs/Chatbot_SSS.pdf",  # Docker volume mount path
        "/docs/Chatbot_SSS.pdf",  # Alternative Docker path
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
    
    print(f"PDF yüklendi: {len(docs)} sayfa")

    # Chunk'lara ayır
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    docs = text_splitter.split_documents(docs)
    
    print(f"Dokuman {len(docs)} chunk'a bölündü")

    # Metadata ekle
    for i, d in enumerate(docs):
        d.metadata["source"] = "Chatbot_SSS.pdf"
        d.metadata["chunk"] = i

    embeddings = OpenAIEmbeddings()

    CONNECTION_STRING = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/chatbot"
    )
    
    print(f"Database bağlantısı: {CONNECTION_STRING}")

    # Mevcut embedding'leri temizle
    try:
        import psycopg
        conn = psycopg.connect(CONNECTION_STRING.replace('postgresql+psycopg://', 'postgresql://'))
        with conn:
            with conn.cursor() as cur:
                # Collection ID'sini al
                cur.execute("SELECT uuid FROM langchain_pg_collection WHERE name = 'chatbot_docs'")
                result = cur.fetchone()
                if result:
                    collection_id = result[0]
                    # Eski embedding'leri sil
                    cur.execute("DELETE FROM langchain_pg_embedding WHERE collection_id = %s", (collection_id,))
                    print("Mevcut embedding'ler temizlendi")
        conn.close()
    except Exception as e:
        print(f"Embedding temizleme hatası (normal olabilir): {e}")

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