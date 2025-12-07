import psycopg2
import os
import sys
from dotenv import load_dotenv

# RAGService에서 차원 정보를 가져오기 위해 경로를 설정합니다.
# 현재 파일 위치에서 'chat' 폴더를 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'chat'))

# RAGService가 있는 'services' 모듈에서 RAGService 클래스를 임포트합니다.
try:
    from services import RAGService
except ImportError as e:
    # services 모듈을 찾을 수 없는 경우를 대비
    print(f"❌ 심각한 임포트 오류: chat/services.py를 찾을 수 없거나 RAGService 클래스 임포트 실패: {e}")
    print("📌 확인 사항: 'chat/services.py' 파일이 존재하며 'RAGService' 클래스가 정의되어 있는지 확인하세요.")
    sys.exit(1)

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "law_db"),
    "user": os.getenv("DB_USER", "law_user"),
    "password": os.getenv("DB_PASSWORD", "1111"),
    "port": os.getenv("DB_PORT", "5432")
}

def reset_rag_table_schema(db_config):
    """
    기존 rag_index_table을 삭제하고, 새로운 768차원 벡터 타입으로 
    테이블을 강제로 다시 생성하며, HNSW 인덱스를 구축합니다.
    또한, chat_lawdocument 테이블에서 불필요한 vector 필드를 제거합니다.
    """
    conn = None
    try:
        if not hasattr(RAGService, 'VECTOR_DIMENSION'):
            raise AttributeError(
                "RAGService 클래스에 'VECTOR_DIMENSION' 상수(예: 768)가 정의되어 있지 않습니다. "
                "chat/services.py 파일을 확인하세요."
            )
        
        dim = RAGService.VECTOR_DIMENSION
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # 1. 원본 테이블(chat_lawdocument)에서 vector 필드 제거 (1단계 목표)
        cur.execute("ALTER TABLE chat_lawdocument DROP COLUMN IF EXISTS vector;")
        print("✅ chat_lawdocument 테이블에서 기존 vector 필드를 제거했습니다.")
        
        # 2. 기존 RAG 인덱스 테이블 강제 삭제 (DROP)
        cur.execute("DROP TABLE IF EXISTS rag_index_table;")
        print("✅ 기존 rag_index_table 테이블 정의가 삭제되었습니다.")
        
        # 3. pgvector 확장(Extension) 존재 확인
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # 4. 새로운 RAG 인덱스 테이블 강제 생성 (CREATE)
        cur.execute(f"""
            CREATE TABLE public.rag_index_table (
                id SERIAL PRIMARY KEY,
                text_chunk TEXT NOT NULL,
                metadata JSONB,
                embedding VECTOR({dim})
            );
        """)
        print(f"✅ rag_index_table이 {dim}차원 벡터 타입으로 새로 생성되었습니다.")
        
        # 5. RAG 검색 성능을 위한 HNSW 인덱스 생성 (필수)
        cur.execute(f"""
            CREATE INDEX idx_rag_embedding_hnsw ON public.rag_index_table 
            USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 128);
        """)
        print("✅ HNSW 벡터 검색 인덱스가 성공적으로 생성되었습니다.")
        
        conn.commit()
        print("\n🎉 데이터베이스 스키마 재설정 완료. 이제 새로운 고품질 데이터로 인덱싱할 준비가 되었습니다.")

    except (Exception, psycopg2.Error) as error:
        print(f"\n데이터베이스 스키마 재설정 중 심각한 오류 발생: {error}")
        if conn:
            conn.rollback() 
            raise

    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    reset_rag_table_schema(DB_CONFIG)