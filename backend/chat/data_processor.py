import json
import numpy as np
import psycopg2 
import os 
from sentence_transformers import SentenceTransformer

# ----------------------------------------------------------------------
# 데이터 전처리 및 임베딩 담당 클래스
# ----------------------------------------------------------------------

class DataProcessor:
    # 최종 안정화 모델: jhgan/ko-sroberta-multitask (768차원)
    VECTOR_DIMENSION = 768 

    def __init__(self, model_name="jhgan/ko-sroberta-multitask"):
        self.embedding_model = SentenceTransformer(model_name)
        self.chunks = []
        self.embeddings = None

    # ----------------------------------------------------------------------
    # 🟢 Load Data Directly from your PostgreSQL DB (chat_lawdocument)
    # ----------------------------------------------------------------------
    def load_data_from_db(self, db_config):
        """
        Loads raw text and metadata from the chat_lawdocument table.
        """
        documents = []
        conn = None
        
        try:
            conn = psycopg2.connect(**db_config)
            cur = conn.cursor()
            
            # document_id, title, case_number, enforcement_date, law_article_no 필드를 메타데이터로 로드
            cur.execute("""
                SELECT 
                    content,         
                    document_id, 
                    title, 
                    case_number, 
                    enforcement_date,
                    law_article_no
                FROM chat_lawdocument
            """)
            
            for row in cur.fetchall():
                content, doc_id, title, case_num, date, article_no = row
                
                metadata = {
                    "document_id": doc_id,
                    "title": title,
                    "case_number": case_num,
                    "enforcement_date": date,
                    "law_article_no": article_no
                }
                
                documents.append({
                    'content': content,
                    'metadata': metadata
                })
            
            cur.close()
            
        except (Exception, psycopg2.Error) as error:
            print(f"Error loading data from PostgreSQL: {error}")
            raise # 오류를 던져서 인덱싱 프로세스를 중단시킵니다.
        finally:
            if conn:
                conn.close()
                
        return documents

    # ----------------------------------------------------------------------
    # 🟢 Text Chunking Logic 
    # ----------------------------------------------------------------------
    def chunk_text(self, text, chunk_size=500, overlap=50):
        """Split text into chunks with overlap"""
        # 기존 로직 유지 (LangChain 대신 기본 split)
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
            
        return chunks
    
    # ----------------------------------------------------------------------
    # 🟢 Embedding Generation 
    # ----------------------------------------------------------------------
    def create_embeddings(self, chunks):
        """Create embeddings for chunks"""
        self.chunks = chunks
        self.embeddings = self.embedding_model.encode(chunks, show_progress_bar=False)
        return self.embeddings