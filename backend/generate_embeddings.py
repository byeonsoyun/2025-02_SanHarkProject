import psycopg2
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import time

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "civil_law_db"),
    "user": os.getenv("DB_USER", "law_user"),
    "password": os.getenv("DB_PASSWORD", "1111"),
    "port": os.getenv("DB_PORT", "5432")
}

def add_vector_column():
    """Add vector column to chat_lawdocument if not exists"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        cur.execute("ALTER TABLE chat_lawdocument ADD COLUMN IF NOT EXISTS embedding vector(768)")
        conn.commit()
        print("✅ Vector column added")
    except Exception as e:
        print(f"❌ Error adding vector column: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def generate_embeddings():
    """Generate embeddings for all documents"""
    print("Loading embedding model...")
    model = SentenceTransformer("jhgan/ko-sroberta-multitask")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Get all documents
    cur.execute("SELECT document_id, title, content FROM chat_lawdocument WHERE embedding IS NULL")
    documents = cur.fetchall()
    total = len(documents)
    
    print(f"Processing {total} documents...")
    
    for idx, (doc_id, title, content) in enumerate(documents, 1):
        # Combine title and content for embedding
        text = f"{title}\n{content}"
        
        # Generate embedding
        embedding = model.encode([text])[0]
        vector_str = "[" + ",".join(map(str, embedding)) + "]"
        
        # Update database
        cur.execute(
            "UPDATE chat_lawdocument SET embedding = %s WHERE document_id = %s",
            (vector_str, doc_id)
        )
        
        if idx % 100 == 0:
            conn.commit()
            print(f"Progress: {idx}/{total} ({idx*100//total}%)")
    
    conn.commit()
    print(f"✅ Completed: {total} embeddings generated")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    print("Step 1: Adding vector column...")
    add_vector_column()
    
    print("\nStep 2: Generating embeddings...")
    start = time.time()
    generate_embeddings()
    elapsed = time.time() - start
    print(f"\n⏱️ Total time: {elapsed:.1f}s")
