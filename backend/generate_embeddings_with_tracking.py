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

def generate_embeddings():
    print("Loading embedding model...")
    model = SentenceTransformer("jhgan/ko-sroberta-multitask")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    cur.execute("SELECT document_id, title, content FROM chat_lawdocument WHERE embedding IS NULL")
    documents = cur.fetchall()
    total = len(documents)
    
    print(f"Processing {total} documents...")
    
    failed = []
    success_count = 0
    
    for idx, (doc_id, title, content) in enumerate(documents, 1):
        try:
            text = f"{title}\n{content}"
            
            # Check for issues
            if not text.strip():
                failed.append((doc_id, "Empty text"))
                continue
            
            if len(text) > 1000000:  # 1MB limit
                failed.append((doc_id, f"Text too long: {len(text)} chars"))
                continue
            
            embedding = model.encode([text])[0]
            vector_str = "[" + ",".join(map(str, embedding)) + "]"
            
            cur.execute(
                "UPDATE chat_lawdocument SET embedding = %s WHERE document_id = %s",
                (vector_str, doc_id)
            )
            success_count += 1
            
            if idx % 100 == 0:
                conn.commit()
                print(f"Progress: {idx}/{total} ({idx*100//total}%) - Success: {success_count}, Failed: {len(failed)}")
                
        except Exception as e:
            failed.append((doc_id, str(e)))
            print(f"❌ Failed on {doc_id}: {e}")
    
    conn.commit()
    
    print(f"\n{'='*60}")
    print(f"✅ Completed: {success_count} embeddings generated")
    print(f"❌ Failed: {len(failed)} documents")
    
    if failed:
        print(f"\n{'='*60}")
        print("Failed documents:")
        for doc_id, reason in failed[:10]:
            print(f"  - {doc_id}: {reason}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")
    
    cur.close()
    conn.close()
    
    return failed

if __name__ == "__main__":
    start = time.time()
    failed = generate_embeddings()
    elapsed = time.time() - start
    print(f"\n⏱️ Total time: {elapsed:.1f}s")
