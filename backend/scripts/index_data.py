import os
import sys
import json
import psycopg2
import numpy as np
from dotenv import load_dotenv

# DataProcessor 클래스 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
from chat.data_processor import DataProcessor 


# ----------------------------------------------------------------------
# 환경 변수 로드 (DB 설정)
# ----------------------------------------------------------------------
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "law_db"),
    "user": os.getenv("DB_USER", "law_user"),
    "password": os.getenv("DB_PASSWORD", "1111"), # 실제 비밀번호로 변경하세요
    "port": os.getenv("DB_PORT", "5432")
}

# ----------------------------------------------------------------------
# 🟢 테이블 및 pgvector 확장 존재 확인 및 생성
# ----------------------------------------------------------------------
def ensure_table_exists(db_config):
    conn = None
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # 1. pgvector 확장 생성
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # 2. rag_index_table 테이블 생성 (768차원 반영)
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS public.rag_index_table (
                id SERIAL PRIMARY KEY,
                text_chunk TEXT NOT NULL,
                metadata JSONB,
                -- DataProcessor의 VECTOR_DIMENSION을 따름 (768)
                embedding VECTOR({DataProcessor.VECTOR_DIMENSION})
            );
        """)
        
        conn.commit()
        print("✅ pgvector 확장(Extension) 및 rag_index_table 테이블 존재 확인/생성 완료.")

    except (Exception, psycopg2.Error) as error:
        print(f"테이블 및 확장 생성 중 심각한 오류 발생: {error}")
        if conn:
            conn.rollback() 
            raise 

    finally:
        if conn:
            cur.close()
            conn.close()


# ----------------------------------------------------------------------
# 🟢 벡터 생성 및 DB 삽입
# ----------------------------------------------------------------------
def insert_embeddings_to_pg(documents, db_config):
    processor = DataProcessor() # 새 모델로 DataProcessor 인스턴스 생성
    conn = None
    
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        print("DB 연결 성공. 벡터 인덱싱 시작...")
        
        insert_count = 0
        
        for doc in documents:
            chunks = processor.chunk_text(doc['content'])
            embeddings = processor.create_embeddings(chunks)
            
            for chunk, embedding in zip(chunks, embeddings):
                # numpy array를 pgvector 문자열 형태로 변환
                vector_str = "[" + ",".join(map(str, embedding)) + "]"
                metadata_json = json.dumps(doc['metadata'], default=str) # datetime 처리 위해 default=str 추가
                
                cur.execute(
                    """
                    INSERT INTO rag_index_table (text_chunk, metadata, embedding)
                    VALUES (%s, %s, %s::vector)
                    """,
                    (chunk, metadata_json, vector_str)
                )
                insert_count += 1

        conn.commit()
        print(f"인덱싱 완료: 총 {insert_count}개의 벡터가 rag_index_table에 삽입되었습니다.")
        
    except (Exception, psycopg2.Error) as error:
        print(f"데이터 삽입 중 심각한 오류 발생: {error}")
        if conn:
            conn.rollback() 
            
    finally:
        if conn:
            cur.close()
            conn.close()


if __name__ == "__main__":
    # 1. DB 연결 및 테이블 존재 확인/생성
    try:
        ensure_table_exists(DB_CONFIG)
    except Exception:
        print("🚨 DB 연결 또는 테이블 생성에 실패하여 인덱싱을 중단합니다.")
        sys.exit(1)
        
    # 2. DataProcessor 인스턴스를 생성하고 DB에서 원본 데이터를 로드합니다.
    data_processor = DataProcessor() # 모델 로딩 (새 모델 다운로드 시도)
    
    try:
        raw_documents = data_processor.load_data_from_db(DB_CONFIG) 
        
        if raw_documents:
            print(f"DB에서 총 {len(raw_documents)}개의 원본 문서를 로드했습니다.")
            # 3. 인덱싱 및 DB 삽입을 시작합니다.
            insert_embeddings_to_pg(raw_documents, DB_CONFIG)
        else:
            print("경고: DB에서 로드된 원본 문서가 없습니다. 인덱싱을 건너뜁니다.")
            
    except Exception as e:
        print(f"초기 데이터 로드 실패: {e}")