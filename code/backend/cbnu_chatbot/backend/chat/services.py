import os
import json
import requests
import numpy as np
from typing import List, Dict, Optional

# Django 관련 임포트
from django.db import connection
from django.db.models import F
from django.conf import settings

# 모델 임포트
from .models import ChbNotice, NoticeRagIndex, ChatMessage

# AI/Vector 라이브러리
from sentence_transformers import SentenceTransformer
from pgvector.django import CosineDistance

# 할루시네이션 방지를 위한 시스템 프롬프트 (충북대 공지사항 특화)
SYSTEM_PROMPT = """
You are a helpful assistant specializing in Chungbuk National University announcements.
You MUST answer based ONLY on the provided context.
You MUST answer in **Korean** language.

당신은 충북대학교 공지사항 안내 챗봇입니다. 아래 원칙을 반드시 지키세요:

1. **언어:** 무조건 **한국어**로만 답변하십시오.
2. **근거 준수:** 제공된 검색 결과에 있는 내용만 사실로 간주하고 답변하세요.
3. **할루시네이션 금지:** 절대 사실이 아닌 내용을 지어내지 마십시오.
4. **답변 스타일:** 
   - 질문에 대한 핵심 정보를 먼저 명확하게 제시
   - 일시, 장소, 대상 등 구체적 정보는 항목별로 정리
   - 마지막에 "이 정보는 충북대학교 공지사항을 통해 확인된 내용입니다." 추가
5. **답변 형식:**

<답변>
질문에 대한 핵심 답변을 먼저 제시

일시: (있는 경우)
장소: (있는 경우)
대상: (있는 경우)
관련 사항: (추가 정보)

이 정보는 충북대학교 공지사항을 통해 확인된 내용입니다.

<출처>
- [게시판] 공지사항 제목
  링크: URL
"""

class RAGService:
    # 임베딩 모델 설정 (Sentence-BERT, 768차원 유지)
    EMBEDDING_MODEL_NAME = "jhgan/ko-sroberta-multitask"
    VECTOR_DIMENSION = 768
    TOP_K = 5  # 검색할 문서 개수

    def __init__(self):
        """서비스 초기화 시 임베딩 모델을 메모리에 로드합니다."""
        print(f"🔄 RAGService: 임베딩 모델({self.EMBEDDING_MODEL_NAME}) 로딩 중...")
        try:
            self.embedder = SentenceTransformer(self.EMBEDDING_MODEL_NAME)
            print("✅ 임베딩 모델 로드 완료.")
        except Exception as e:
            print(f"❌ 임베딩 모델 로드 실패: {e}")
            self.embedder = None
        
        # Ollama 설정
        self.ollama_url = getattr(settings, 'LLM_API_URL', 'http://127.0.0.1:11434/api/generate')
        self.ollama_model = getattr(settings, 'LLM_MODEL_NAME', 'llama3')
        print(f"🔗 Ollama: {self.ollama_url} (모델: {self.ollama_model})")

    # ==========================================================
    # 1. 인덱싱(Indexing) 관련 메서드 (관리자용)
    # ==========================================================

    @staticmethod
    def clear_rag_index():
        """
        RAG 인덱스 테이블(NoticeRagIndex)을 완전히 비우고 ID를 초기화합니다.
        데이터 재구축 시 사용합니다. PostgreSQL TRUNCATE를 사용합니다.
        """
        RAG_TABLE_NAME = NoticeRagIndex._meta.db_table # 'notice_rag_index_table'
        try:
            with connection.cursor() as cursor:
                # 테이블 데이터 삭제 및 시퀀스 초기화 (PostgreSQL 전용)
                cursor.execute(f"TRUNCATE TABLE {RAG_TABLE_NAME} RESTART IDENTITY CASCADE;")
            print(f"🗑️ RAG 인덱스 테이블({RAG_TABLE_NAME})이 성공적으로 초기화되었습니다.")
            return True
        except Exception as e:
            print(f"❌ RAG 인덱스 초기화 실패: {e}")
            return False

    def embed_and_index_documents(self):
        """
        ChbNotice(원본) 테이블에서 데이터를 가져와 임베딩 후 NoticeRagIndex(검색용)에 저장합니다.
        """
        if not self.embedder:
            print("❌ 임베딩 모델이 로드되지 않아 작업을 수행할 수 없습니다.")
            return 0

        # 1. 원본 데이터 가져오기 (ChbNotice 모델 사용)
        # 전체 문서를 대상으로 인덱싱을 수행한다고 가정
        source_docs = ChbNotice.objects.all() 
        total_docs = source_docs.count()
        
        if total_docs == 0:
            print("⚠️ ChbNotice 테이블이 비어있습니다. 크롤링을 먼저 수행하세요.")
            return 0

        print(f"📦 총 {total_docs}건의 공지사항 문서 인덱싱을 시작합니다...")
        
        batch_data = []
        success_count = 0

        # 청킹 로직이 없으므로, 원본 공지사항 하나당 하나의 청크로 처리합니다.
        for doc in source_docs:
            content = doc.content
            
            # 유효성 검사 (너무 짧은 텍스트 제외)
            if not content or len(content) < 20: 
                continue

            try:
                # 2. 임베딩 생성 (벡터화)
                # SentenceTransformer는 numpy array를 반환합니다.
                vector = self.embedder.encode(content)
                
                # 3. 메타데이터 구성 (JSON)
                metadata = {
                    "notice_id": doc.notice_id,
                    "title": doc.title,
                    "board_type": doc.board_type,
                    "post_date": str(doc.post_date), # 날짜는 문자열로 변환
                    "source_url": doc.source_url
                }

                # 4. 저장할 객체 생성 (NoticeRagIndex 모델 사용)
                rag_obj = NoticeRagIndex(
                    text_chunk=content,
                    metadata=metadata,
                    embedding=vector.tolist()  # numpy array -> list 변환
                )
                batch_data.append(rag_obj)
                success_count += 1

                # 500개씩 끊어서 DB에 저장 (Bulk Insert)
                if len(batch_data) >= 500:
                    NoticeRagIndex.objects.bulk_create(batch_data)
                    batch_data = []
                    print(f"   ... {success_count}건 처리 완료")

            except Exception as e:
                print(f"   ❌ 공지 ID {doc.notice_id} 처리 중 오류: {e}")

        # 남은 데이터 저장
        if batch_data:
            NoticeRagIndex.objects.bulk_create(batch_data)
        
        # 5. 성능 최적화를 위한 HNSW 인덱스 생성
        # bulk_create 후 실행하는 것이 좋습니다.
        self._create_hnsw_index_on_embedding()

        print(f"🎉 인덱싱 완료! 총 {success_count}건의 벡터가 NoticeRagIndex 테이블에 저장되었습니다.")
        return success_count

    def _create_hnsw_index_on_embedding(self):
        """pgvector 검색 성능 최적화를 위해 HNSW 인덱스를 생성합니다."""
        # Django ORM은 HNSW 인덱스 생성을 직접 지원하지 않아 raw SQL을 사용합니다.
        RAG_TABLE_NAME = NoticeRagIndex._meta.db_table
        with connection.cursor() as cursor:
            # vector_cosine_ops는 코사인 유사도 검색을 위한 연산자입니다.
            sql = f"CREATE INDEX IF NOT EXISTS notice_rag_hnsw_index ON {RAG_TABLE_NAME} USING hnsw (embedding vector_cosine_ops);"
            print(f"🔄 HNSW 인덱스 생성 시도: {sql}")
            try:
                cursor.execute(sql)
                print("✅ HNSW 인덱스 생성 또는 확인 완료.")
            except Exception as e:
                print(f"❌ HNSW 인덱스 생성 실패: {e}. pgvector 확장이 활성화되었는지 확인하세요.")


    # ==========================================================
    # 2. 검색(Retrieval) 관련 메서드 (사용자 서비스용)
    # ==========================================================

    def retrieve_context(self, query: str) -> List[Dict]:
        """
        사용자의 질문과 가장 유사한 공지사항 문서를 DB에서 검색합니다.
        NoticeRagIndex 모델을 사용하여 검색합니다.
        """
        if not self.embedder:
            return []

        try:
            # 1. 질문 임베딩
            # SentenceTransformer의 encode는 numpy array를 반환하므로 tolist()로 변환
            query_vector = self.embedder.encode(query).tolist()

            # 2. 벡터 유사도 검색 (Django ORM + pgvector)
            # CosineDistance를 사용하면 거리가 0에 가까울수록 유사도가 높습니다.
            results_queryset = NoticeRagIndex.objects.annotate(
                distance=CosineDistance('embedding', query_vector)
            ).order_by('distance')

            
            # 3. Retrieval Post-Filter (검색 결과 필터링 및 우선순위 조정)
            # "기숙사 신청"처럼 일반적인 질문에 대해, 너무 기간이 명확한 임시 공지(하기/특별개관)를 제외하여 정확도를 높입니다.
            
            # 사용자 쿼리가 일반적인 '기숙사' 질문인지 확인
            is_general_dorm_query = '기숙사' in query and not any(k in query for k in ['특별개관', '하기', '여름', '겨울', '특이'])
            
            final_results = []
            
            # 쿼리셋을 리스트로 변환하여 순회 (top K개만 먼저 가져옴)
            for item in results_queryset[:self.TOP_K * 2]: # 일단 TOP_K의 2배를 가져와서 필터링
                item_dict = {
                    "text": item.text_chunk,
                    "metadata": item.metadata,
                    "score": 1 - item.distance
                }
                
                title = item_dict['metadata'].get('title', '')

                # 일반적인 기숙사 질문인데, '특별개관'이나 '계절'과 같은 임시/특정 기간 공지라면 제외
                if is_general_dorm_query and ('특별개관' in title or '계절' in title):
                    # 임시 공지 제외
                    continue
                    
                final_results.append(item_dict)
                
                # 필요한 TOP_K 개수에 도달하면 종료
                if len(final_results) >= self.TOP_K:
                    break
                    
            return final_results

        except Exception as e:
            print(f"❌ 검색(Retrieval) 중 오류 발생: {e}")
            return []

    # ==========================================================
    # 3. 복잡도 감지 (민사법 시스템에서 이식)
    # ==========================================================
    
    def _regex_filter(self, question: str) -> Optional[str]:
        """1단계: 정규표현식 기반 초고속 필터링"""
        import re
        
        # 명확한 패턴 검출
        patterns = {
            'date': r'\d{4}[-./년]\d{1,2}[-./월]\d{1,2}',  # 날짜
            'number': r'제?\s*\d+\s*[호회차기]',  # 제N호, N회차
            'keyword': r'(공지|안내|모집|신청|접수|마감)'  # 명확한 키워드
        }
        
        for pattern_type, pattern in patterns.items():
            if re.search(pattern, question):
                print(f"⚡ Regex 필터: '{pattern_type}' 패턴 감지 → 단순 검색")
                return "search"
        
        return None
    
    def _llm_router(self, question: str) -> str:
        """2단계: LLM 기반 쿼리 라우터"""
        router_prompt = f"""너는 충북대학교 공지사항 챗봇의 쿼리 라우터이다.
사용자 질문을 분석하여 다음 두 가지 중 하나로 분류하고, 반드시 JSON 형식으로만 대답해라.

- search: 공지사항 검색, 날짜 확인, 단순 정보 조회 등 명확한 사실을 묻는 경우
- complex: 비교 분석, 추천, 설명 요청, 조언 등 추론이 필요한 경우

질문: "{question}"

답변 형식: {{"type": "search"}} 또는 {{"type": "complex"}}"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.ollama_model,
                    "prompt": router_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 50
                    }
                },
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', '').strip()
                
                # JSON 파싱
                import re
                json_match = re.search(r'\{[^}]+\}', answer)
                if json_match:
                    route_data = json.loads(json_match.group())
                    route_type = route_data.get('type', 'complex')
                    print(f"🤖 LLM Router: {route_type}")
                    return route_type
                
                # JSON 파싱 실패 시 키워드 기반 폴백
                if 'search' in answer.lower():
                    return 'search'
                    
        except Exception as e:
            print(f"⚠️ LLM Router 오류: {e}")
        
        # 오류 시 안전하게 complex로 처리
        return 'complex'
    
    def needs_llm_analysis(self, question: str) -> bool:
        """하이브리드 라우팅: Regex → LLM Router"""
        print(f"🔍 하이브리드 라우팅 시작: {question}")
        
        # 1단계: Regex 필터
        regex_result = self._regex_filter(question)
        if regex_result == "search":
            return False
        
        # 2단계: LLM Router
        route_type = self._llm_router(question)
        
        is_complex = (route_type == "complex")
        print(f"   → 최종 판단: {'복잡한 질의 (LLM 사용)' if is_complex else '단순 검색'}")
        
        return is_complex
    
    def create_simple_summary(self, query: str, results: List[Dict]) -> str:
        """단순 검색 결과를 구조화된 형식으로 반환"""
        if not results:
            return "관련 공지사항을 찾을 수 없습니다."
        
        # 답변 섹션 (첫 번째 결과의 내용 요약)
        first_doc = results[0]
        content_preview = first_doc['text'][:300].replace('\n', ' ').strip()
        
        summary = f"<답변>\n"
        summary += f"'{query}'에 대한 검색 결과 {len(results)}건을 찾았습니다.\n\n"
        summary += f"{content_preview}...\n\n"
        summary += f"자세한 내용은 아래 출처를 참고해주세요.\n\n"
        
        # 출처 섹션
        summary += f"<출처>\n"
        for i, doc in enumerate(results, 1):
            meta = doc['metadata']
            title = meta.get('title', '제목 없음')
            board_type = meta.get('board_type', '일반')
            post_date = meta.get('post_date', 'N/A')
            url = meta.get('source_url', '#')
            summary += f"{i}. [{board_type}] {title}\n   게시일: {post_date}\n   링크: {url}\n\n"
        
        return summary

    # ==========================================================
    # 4. 생성(Generation) 관련 메서드 (LLM 호출)
    # ==========================================================

    def generate_answer(self, user_query: str, recent_chats=None) -> Dict:
        """
        RAG 파이프라인 전체를 실행합니다. (검색 -> 프롬프트 조합 -> LLM 답변)
        """
        # 1. 검색
        retrieved_docs = self.retrieve_context(user_query)
        print(f"\n🔍 [검색된 공지사항 Top {len(retrieved_docs)} / 총 {len(retrieved_docs)}건]")
        if retrieved_docs:
            for i, doc in enumerate(retrieved_docs):
                title = doc['metadata'].get('title', '제목 없음')
                score = doc.get('score', 'N/A')
                print(f"[{i+1}] {title} (유사도: {score:.4f})")
                print(f"   게시판: {doc['metadata'].get('board_type', 'N/A')}, 게시일: {doc['metadata'].get('post_date', 'N/A')}")
                print(f"   내용 일부: {doc['text'][:80]}...\n")
        else:
            print("   --> 검색된 공지사항이 없습니다.")
        
        # 2. 문맥 조합
        if not retrieved_docs:
            return {
                "answer": "죄송합니다. 데이터베이스에서 관련 공지사항 정보를 찾을 수 없어 답변을 드릴 수 없습니다. 질문을 바꿔주시거나, 공지사항을 확인해 보세요.",
                "sources": []
            }

        context_text = "\n\n".join(
            [f"문서[{i+1}]: {doc['text']} (출처: {doc['metadata'].get('title', '제목 없음')} / URL: {doc['metadata'].get('source_url', '링크 없음')})" 
             for i, doc in enumerate(retrieved_docs)]
        )
        
        # 이전 대화 맥락 추가
        chat_context = ""
        if recent_chats:
            chat_context = "\n\n[이전 대화 맥락]\n" + "\n".join([
                f"사용자: {chat.content if chat.role == 'user' else ''}\n챗봇: {chat.content if chat.role == 'assistant' else ''}"
                for chat in reversed(list(recent_chats))
            ])

        # 3. 프롬프트 구성 (공지사항 기반으로 변경)
        full_prompt = f"""
{SYSTEM_PROMPT}

{chat_context}

[검색된 공지사항 근거]
{context_text}

[사용자 질문]
{user_query}

[지시사항]
위 [검색된 공지사항 근거]를 바탕으로 [사용자 질문]에 대해 **한국어**로 친절하게 답변하세요. 
**가장 관련된 문서를 명시적으로 언급하며 답변을 시작하십시오.** (예: "문서[3]에 따르면...")
답변 끝에 관련 공지사항의 제목과 URL을 **간결한 목록 형태**로 반드시 명시해 주세요. (예: 출처: [제목](URL))

[답변 (한국어)]:
"""

        # 4. Ollama LLM 호출 (settings.py의 값 사용)
        OLLAMA_API_URL = getattr(settings, 'LLM_API_URL', "http://localhost:11434/api/generate")
        OLLAMA_MODEL_NAME = getattr(settings, 'LLM_MODEL_NAME', "llama3")

        print(f"🤖 LLM 생성 요청 중... (모델: {OLLAMA_MODEL_NAME})")
        try:
            payload = {
                "model": OLLAMA_MODEL_NAME,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1, # 창의성 억제
                    "num_predict": 1024, # 답변 길이 확보
                    "stop": ["User:", "System:"] # 이상한 반복 방지
                }
            }
            # 요청 타임아웃 60초 설정
            response = requests.post(OLLAMA_API_URL, json=payload, timeout=60) 
            response.raise_for_status() # HTTP 오류 발생 시 예외 발생
            
            result_json = response.json()
            answer = result_json.get("response", "오류: LLM 응답이 비어있습니다.")

            return {
                "answer": answer,
                # 소스 메타데이터를 프론트엔드로 전달
                "sources": [doc['metadata'] for doc in retrieved_docs]
            }

        except requests.exceptions.Timeout:
            print("❌ LLM 호출 시간 초과")
            return {
                "answer": "죄송합니다. LLM 서버와의 통신 시간이 초과되었습니다. 서버 상태를 확인해 주세요.",
                "sources": []
            }
        except requests.exceptions.RequestException as e:
            print(f"❌ LLM 호출 실패 (네트워크/HTTP 오류): {e}")
            return {
                "answer": f"죄송합니다. LLM 서버 호출 중 오류가 발생했습니다. (오류: {e}). Ollama 서버 상태 및 URL 설정을 확인해 주세요.",
                "sources": []
            }
        except Exception as e:
            print(f"❌ 기타 LLM 호출 실패: {e}")
            return {
                "answer": "죄송합니다. 답변 생성 중 알 수 없는 오류가 발생했습니다. 로그를 확인해 주세요.",
                "sources": []
            }