import psycopg2
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv() 

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "civil_law_db"),
    "user": os.getenv("DB_USER", "law_user"),
    "password": os.getenv("DB_PASSWORD", "1111"),
    "port": os.getenv("DB_PORT", "5432")
}

_model = None

def get_embedding_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("jhgan/ko-sroberta-multitask")
    return _model

def search_pgvector(query: str, k: int = 5):
    """Vector similarity search on chat_lawdocument table"""
    model = get_embedding_model()
    query_embedding = model.encode([query])[0]
    query_vector_str = "[" + ",".join(map(str, query_embedding)) + "]"
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    cur.execute(
        f"""
        SELECT document_id, title, content, doc_type, 
               embedding <-> '{query_vector_str}' AS distance
        FROM chat_lawdocument
        WHERE embedding IS NOT NULL
        ORDER BY distance
        LIMIT {k}
        """
    )
    
    results = []
    for row in cur.fetchall():
        doc_id, title, content, doc_type, distance = row
        results.append({
            "document_id": doc_id,
            "title": title,
            "content": content,
            "doc_type": doc_type,
            "distance": distance
        })
    
    cur.close()
    conn.close()
    return results

if __name__ == "__main__":
    test_query = "계약 위반 시 손해배상 청구"
    print(f"테스트 쿼리: {test_query}\n")
    
    results = search_pgvector(test_query, k=3)
    
    if results:
        print(f"✅ {len(results)}개 결과 발견\n")
        for i, r in enumerate(results, 1):
            print(f"--- 결과 {i} (거리: {r['distance']:.4f}) ---")
            print(f"제목: {r['title']}")
            print(f"유형: {r['doc_type']}")
            print(f"내용: {r['content'][:150]}...\n")
    else:
        print("❌ 결과 없음")
