"""
Scalable database search system with vector similarity
"""
import os
import sys
from pathlib import Path
import psycopg2
from sentence_transformers import SentenceTransformer
from .ollama_client import OllamaClient
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "civil_law_db"),
    "user": os.getenv("DB_USER", "law_user"),
    "password": os.getenv("DB_PASSWORD", "1111"),
    "port": os.getenv("DB_PORT", "5432")
}

class LegalDBSearch:
    def __init__(self):
        base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        model = os.getenv('OLLAMA_MODEL', 'llama3.2')
        self.ollama_client = OllamaClient(base_url=base_url, model=model)
        self.embedding_model = None
        print(f"🔗 Ollama: {base_url} (모델: {model})")
    
    def _get_embedding_model(self):
        if self.embedding_model is None:
            self.embedding_model = SentenceTransformer("jhgan/ko-sroberta-multitask")
        return self.embedding_model
    
    def search_legal_documents(self, query, limit=5):
        """Vector similarity search"""
        model = self._get_embedding_model()
        query_embedding = model.encode([query])[0]
        vector_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute(
            f"""
            SELECT document_id, title, content, doc_type, 
                   embedding <-> '{vector_str}' AS distance
            FROM chat_lawdocument
            WHERE embedding IS NOT NULL
            ORDER BY distance
            LIMIT {limit}
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
    
    def generate_answer_with_context(self, question, search_results, recent_chats):
        """Generate answer with conversation context"""
        context_text = "\n\n".join([
            f"[{r['doc_type']}] {r['title']}\n{r['content'][:500]}"
            for r in search_results[:3]
        ])
        
        chat_context = ""
        if recent_chats:
            chat_context = "\n이전 대화:\n" + "\n".join([
                f"Q: {chat.question}\nA: {chat.answer[:100]}..."
                for chat in reversed(list(recent_chats))
            ])
        
        prompt = f"""당신은 민사법 전문가입니다. 다음 법률 자료를 바탕으로 질문에 답변하세요.

{chat_context}

관련 법률 자료:
{context_text}

질문: {question}

답변 (한국어로만 작성):"""
        
        return self.ollama_client.generate_response(prompt)
    
    def _create_enhanced_summary(self, query, results):
        """Create structured summary for simple queries"""
        if not results:
            return "관련 정보를 찾을 수 없습니다."
        
        summary = f"'{query}' 검색 결과 ({len(results)}건):\n\n"
        
        for i, r in enumerate(results[:3], 1):
            summary += f"{i}. [{r['doc_type']}] {r['title']}\n"
            summary += f"   {r['content'][:200]}...\n\n"
        
        return summary

# Global instance
legal_search = LegalDBSearch()
