import os
import json
import requests
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta

# Django 관련 임포트
from django.db import connection
from django.db.models import F
from django.conf import settings

# 모델 임포트
from .models import ChbNotice, NoticeRagIndex, ChatMessage

# AI/Vector 라이브러리
from sentence_transformers import SentenceTransformer
from pgvector.django import CosineDistance

# 할루시네이션 방지를 위한 시스템 프롬프트 (충북대 정보 통합)
SYSTEM_PROMPT = """
You are a helpful assistant specializing in Chungbuk National University information.
You MUST answer based ONLY on the provided context.
You MUST answer in **Korean** language.

당신은 충북대학교 정보 안내 챗봇입니다. 아래 원칙을 반드시 지키세요:

1. **언어:** 무조건 **한국어**로만 답변하십시오.
2. **근거 준수:** 제공된 검색 결과에 있는 내용만 사실로 간주하고 답변하세요.
3. **할루시네이션 금지:** 절대 사실이 아닌 내용을 지어내지 마십시오.
4. **동아리 질문 특별 규칙:**
   - 제공된 문서에 나열된 **모든 동아리**를 빠짐없이 답변에 포함하세요
   - 문서를 처음부터 끝까지 읽고 각 동아리를 순서대로 나열하세요
   - 절대로 일부 동아리만 선택하거나 생략하지 마세요
   - 문서에 없는 동아리는 절대 만들어내지 마세요
5. **정보 유형 구분:**
   - 학사일정: 개강일, 종강일, 시험기간, 방학, 수강신청 등
   - 공지사항: 학교/학과 공지, 모집, 안내사항 등
   - 기숙사 정보: 연락처, 위치, 식단, 기숙사 공지사항 등
6. **식단 답변 시 절대 규칙:**
   - "안녕하세요", "여러분" 같은 인사말 절대 금지
   - 각 요일에 반드시 날짜 포함 (예: **월요일 (2025-12-09)**)
   - 메뉴를 요약하거나 생략하지 말고 문서 그대로 복사
7. **학년도 구분 중요:**
   - 1학기(3월~8월): 해당 연도가 학년도 (예: 2025년 6월 = 2025학년도 1학기)
   - 2학기(9월~2월): 해당 연도가 학년도 (예: 2024년 12월 = 2024학년도 2학기, 2025년 1월 = 2024학년도 2학기)
   - 사용자가 "2025학년도 2학기"를 물으면 2025년 12월~2026년 2월 정보를 찾아야 함
   - 게시일이 2024년 12월이면 "2024학년도 2학기" 정보임
8. **일정 추가 요청 감지:** 
   사용자가 "일정 추가", "캘린더에 추가", "일정 등록", "일정 넣어줘", "추가해줘" 등의 명시적 요청을 하면 
   반드시 답변 마지막에 다음 형식을 정확히 포함하세요:
   
   [EVENT_ADD]{"title": "일정제목", "start_date": "2025-12-05", "end_date": "2025-12-05", "description": "설명"}[/EVENT_ADD]
   
   예시:
   - "내일 중간고사 일정 추가해줘" → [EVENT_ADD]{"title": "중간고사", "start_date": "2025-12-06", "end_date": "2025-12-06", "description": "중간고사"}[/EVENT_ADD]
   - "12월 25일 크리스마스 파티 추가" → [EVENT_ADD]{"title": "크리스마스 파티", "start_date": "2025-12-25", "end_date": "2025-12-25", "description": "크리스마스 파티"}[/EVENT_ADD]
   
   **중요**: 
   - "언제야?", "알려줘", "뭐야?" 같은 단순 질문에는 [EVENT_ADD]를 절대 사용하지 마세요.
   - 오직 "추가", "등록", "넣어줘" 같은 명령어가 있을 때만 사용하세요.

9. **답변 스타일:** 
   - 질문에 대한 핵심 정보를 먼저 명확하게 제시
   - 일시, 장소, 대상 등 구체적 정보는 항목별로 정리
   - **마크업 절대 금지**: 순수 텍스트로만 답변하세요
   - 금지 목록: <br>, </br>, <strong>, </strong>, <b>, </b>, <em>, <i>, <u>, <h1>~<h6>, <ul>, <ol>, <li>, <a>, <p>, <div>, <span>, <table>, <tr>, <td>, <hr>, <code>, <pre>, &nbsp;, **, __, ##, 등 모든 HTML/마크다운 마크업
   - 줄바꿈은 일반 텍스트 줄바꿈만 사용
   - 마지막에 정보 출처를 명시
10. **답변 형식:**

질문에 대한 핵심 답변을 먼저 제시

일시: (있는 경우)
장소: (있는 경우)
대상: (있는 경우)
관련 사항: (추가 정보)

이 정보는 충북대학교 [학사일정/공지사항/기숙사 안내]를 통해 확인된 내용입니다.

[출처]
반드시 각 공지사항의 URL을 포함하여 다음 형식으로 작성하세요:
- [게시판 유형] 제목
  URL: https://www.cbnu.ac.kr/... (전체 URL 필수)

예시:
- [전체공지] 2025학년도 2학기 학부 교내장학금 신청 안내
  URL: https://www.cbnu.ac.kr/www/selectBbsNttView.do?key=813&bbsNo=8&nttNo=158484
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
    
    def _get_week_dates_map(self, base_date=None):
        """
        기준 날짜가 포함된 주의 월~일 날짜를 정확히 계산하여 딕셔너리로 반환
        LLM이 날짜를 계산하지 않고 이 값을 그대로 사용하도록 유도
        """
        if base_date is None:
            base_date = datetime.now()
        
        # 현재 요일(0:월 ~ 6:일)을 기준으로 이번 주 월요일 계산
        monday_date = base_date - timedelta(days=base_date.weekday())
        
        week_map = {}
        days_name = ["월", "화", "수", "목", "금", "토", "일"]
        
        for i, day_name in enumerate(days_name):
            current_day = monday_date + timedelta(days=i)
            week_map[day_name] = current_day.strftime("%Y-%m-%d")
            
        return week_map

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

                # 4. 저장할 객체 생성 - 직접 SQL 사용
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO notice_rag_index_table (notice_id, chunk_index, text, embedding) VALUES (%s, %s, %s, %s)",
                        [doc.notice_id, 0, content, vector.tolist()]
                    )
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

        # 동아리 질문 하드코딩
        if '동아리' in query:
            print("🎯 동아리 질문 감지 - 하드코딩 데이터 반환")
            try:
                from .models import ChbNotice
                club_notice = ChbNotice.objects.get(notice_id='sw_static_커뮤니티_동아리소개_상세')
                print(f"✅ 동아리 데이터 찾음: {club_notice.title}, 길이: {len(club_notice.content)}자")
                return [{
                    'text': club_notice.content,
                    'metadata': {
                        'notice_id': club_notice.notice_id,
                        'title': club_notice.title,
                        'board_type': club_notice.board_type,
                        'post_date': str(club_notice.post_date),
                        'source_url': 'https://software.cbnu.ac.kr/sub040301'
                    },
                    'score': 0.99,
                    'semester_match': False
                }]
            except Exception as e:
                print(f"❌ 동아리 데이터 로드 실패: {e}")
        
        # 졸업요건 질문 하드코딩
        if '졸업요건' in query or '졸업 요건' in query:
            print("🎯 졸업요건 질문 감지 - 하드코딩 데이터 반환")
            try:
                from .models import ChbNotice
                
                # 학번 추출
                import re
                year_match = re.search(r'(21|22|23|24|25)학번', query)
                
                if year_match:
                    year = year_match.group(1) + '학번'
                    grad_notice = ChbNotice.objects.get(notice_id=f'sw_static_졸업요건_{year}')
                    print(f"✅ {year} 졸업요건 데이터 찾음")
                    return [{
                        'text': grad_notice.content,
                        'metadata': {
                            'notice_id': grad_notice.notice_id,
                            'title': grad_notice.title,
                            'board_type': grad_notice.board_type,
                            'post_date': str(grad_notice.post_date),
                            'source_url': grad_notice.source_url
                        },
                        'score': 0.99,
                        'semester_match': False
                    }]
                else:
                    # 학번 미지정 시 모든 졸업요건 반환
                    grad_notices = ChbNotice.objects.filter(
                        notice_id__startswith='sw_static_졸업요건_'
                    ).order_by('notice_id')
                    
                    results = []
                    for notice in grad_notices:
                        results.append({
                            'text': notice.content,
                            'metadata': {
                                'notice_id': notice.notice_id,
                                'title': notice.title,
                                'board_type': notice.board_type,
                                'post_date': str(notice.post_date),
                                'source_url': notice.source_url
                            },
                            'score': 0.99,
                            'semester_match': False
                        })
                    
                    print(f"✅ 졸업요건 데이터 {len(results)}개 찾음")
                    return results
                    
            except Exception as e:
                print(f"❌ 졸업요건 데이터 로드 실패: {e}")
        
        # 교수/연구실 질문 하드코딩
        if '교수' in query or '연구실' in query or '교원' in query:
            print("🎯 교수/연구실 질문 감지 - 하드코딩 데이터 반환")
            try:
                from .models import ChbNotice
                lab_notice = ChbNotice.objects.get(notice_id='sw_static_대학원_연구실소개')
                print(f"✅ 연구실 데이터 찾음: {lab_notice.title}")
                return [{
                    'text': lab_notice.content,
                    'metadata': {
                        'notice_id': lab_notice.notice_id,
                        'title': lab_notice.title,
                        'board_type': lab_notice.board_type,
                        'post_date': str(lab_notice.post_date),
                        'source_url': lab_notice.source_url
                    },
                    'score': 0.99,
                    'semester_match': False
                }]
            except Exception as e:
                print(f"❌ 연구실 데이터 로드 실패: {e}")

        try:
            # 1. 질문 임베딩
            query_vector = self.embedder.encode(query).tolist()
            
            # "최근" 키워드 감지 - 3개월 이내로 제한
            is_recent_query = any(kw in query for kw in ['최근', '최신', '요즘', '이번'])
            search_limit = self.TOP_K * 30 if is_recent_query else self.TOP_K * 5

            # 2. 벡터 유사도 검색 (Raw SQL)
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT r.text, r.notice_id, r.embedding <=> %s::vector as distance
                    FROM notice_rag_index_table r
                    ORDER BY distance
                    LIMIT %s
                """, [query_vector, search_limit])
                
                raw_results = cursor.fetchall()
            
            # 공지사항 정보 가져오기
            from .models import ChbNotice
            from datetime import datetime, timedelta
            
            notice_ids = [row[1] for row in raw_results]
            notices = {n.notice_id: n for n in ChbNotice.objects.filter(notice_id__in=notice_ids)}
            
            # 3. Retrieval Post-Filter
            is_general_dorm_query = '기숙사' in query and not any(k in query for k in ['특별개관', '하기', '여름', '겨울', '특이'])
            is_menu_query = any(keyword in query for keyword in ['식단', '메뉴', '오늘 밥', '이번주 식단'])
            
            # 소프트웨어학과 명시 여부 확인
            is_software_explicit = '소프트웨어' in query
            
            final_results = []
            menu_results = []
            
            # 최근 키워드 시 3개월 기준
            three_months_ago = datetime.now() - timedelta(days=90)
            
            for text, notice_id, distance in raw_results:
                if notice_id not in notices:
                    continue
                    
                notice = notices[notice_id]
                
                # 소프트웨어 명시 없으면 소프트웨어학과 데이터 제외
                if not is_software_explicit and notice.board_type and '소프트웨어' in notice.board_type:
                    continue
                
                # 최근 키워드 시 3개월 이내만
                if is_recent_query and notice.post_date < three_months_ago.date():
                    continue
                
                item_dict = {
                    "text": text,
                    "metadata": {
                        "notice_id": notice.notice_id,
                        "title": notice.title,
                        "board_type": notice.board_type,
                        "post_date": str(notice.post_date),
                        "source_url": notice.source_url
                    },
                    "score": 1 - distance
                }
                
                title = notice.title

                # 식단 질문인 경우 식단표만 수집
                if is_menu_query:
                    if '식단표' in title:
                        menu_results.append(item_dict)
                    elif any(exclude in title for exclude in ['급식제도', '납부', '선택', '환불', '퇴거']):
                        continue
                    else:
                        final_results.append(item_dict)
                else:
                    if is_general_dorm_query and ('특별개관' in title or '계절' in title):
                        continue
                    final_results.append(item_dict)
                
                if is_menu_query and len(menu_results) >= 3:
                    break
                    
                if len(final_results) >= self.TOP_K:
                    break
            
            # 식단 질문인 경우 식단표를 최우선으로
            if is_menu_query and menu_results:
                building_keywords = {'본관': '본관', '양성재': '양성재', '양진재': '양진재', '양현재': '양현재'}
                target_building = None
                for keyword, building in building_keywords.items():
                    if keyword in query:
                        target_building = building
                        break
                
                if target_building:
                    filtered_menu = [m for m in menu_results if target_building in m['metadata']['title']]
                    if filtered_menu:
                        menu_results = filtered_menu
                        print(f"🍽️ {target_building} 식단만 필터링: {len(menu_results)}건")
                
                final_results = menu_results + final_results[:max(0, self.TOP_K - len(menu_results))]
                print(f"🍽️ 식단 질문 감지: 식단표 {len(menu_results)}건 우선 반환")
            else:
                # 공모전 등 복수 결과 필요 시 최소 2개 반환
                min_results = 2 if any(kw in query for kw in ['공모전', '대회', '모집']) else self.TOP_K
                final_results = final_results[:max(min_results, self.TOP_K)]
            
            # 현재 학기 판단
            current_month = datetime.now().month
            if 3 <= current_month <= 8:
                current_semester = "1학기"
                current_year = datetime.now().year
            else:
                current_semester = "2학기"
                current_year = datetime.now().year if current_month >= 9 else datetime.now().year - 1
            
            # 현재 학기 공지 우선순위 부여 (모든 질문에 적용)
            for r in final_results:
                title = r['metadata']['title']
                if f"{current_year}학년도" in title and current_semester in title:
                    r['semester_match'] = True
                else:
                    r['semester_match'] = False
            
            # 학기 일치 여부로 정렬 (일치하는 것 우선)
            final_results.sort(key=lambda x: (x.get('semester_match', False), x.get('score', 0)), reverse=True)
            
            # "최근" 키워드가 있으면 2개월 이내 공지만 필터링
            is_recent_query = any(kw in query for kw in ['최근', '최신', '요즘', '이번'])
            if is_recent_query:
                two_months_ago = datetime.now().date() - timedelta(days=60)
                recent_filtered = [r for r in final_results 
                                  if datetime.strptime(r['metadata']['post_date'], '%Y-%m-%d').date() >= two_months_ago]
                
                final_results = recent_filtered
                print(f"📅 '최근' 키워드 감지: {two_months_ago} 이후 공지 {len(final_results)}건 반환")
                    
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
        router_prompt = f"""너는 충북대학교 정보 안내 챗봇의 쿼리 라우터이다.
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
        
        summary = f"'{query}'에 대한 검색 결과 {len(results)}건을 찾았습니다.\n\n"
        summary += f"{content_preview}...\n\n"
        summary += f"자세한 내용은 아래 출처를 참고해주세요.\n\n"
        
        # 출처 섹션
        summary += f"[출처]\n"
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
        from datetime import datetime
        import re
        
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month
        
        # 학년도 계산
        if current_month >= 3 and current_month <= 8:
            current_academic_year = current_year
            current_semester = f"{current_academic_year}학년도 1학기"
            semester_period = f"{current_year}년 3월~8월"
        elif current_month >= 9:
            current_academic_year = current_year
            current_semester = f"{current_academic_year}학년도 2학기"
            semester_period = f"{current_year}년 9월~{current_year+1}년 2월"
        else:  # 1~2월
            current_academic_year = current_year - 1
            current_semester = f"{current_academic_year}학년도 2학기"
            semester_period = f"{current_year-1}년 9월~{current_year}년 2월"
        
        # 사용자가 요청한 학년도 추출
        year_match = re.search(r'(\d{4})학년도', user_query)
        requested_year = int(year_match.group(1)) if year_match else current_academic_year
        
        # 검색된 문서 필터링 (요청한 학년도와 일치하는 것만)
        if year_match:
            filtered_docs = []
            for doc in retrieved_docs:
                doc_content = doc['text']
                # 문서에 학년도 정보가 있으면 확인
                if f"{requested_year}학년도" in doc_content or f"{requested_year}학년도" in doc['metadata'].get('title', ''):
                    filtered_docs.append(doc)
                # 학년도 정보가 없으면 날짜로 판단
                elif '학년도' not in doc_content:
                    post_date_str = doc['metadata'].get('post_date', '')
                    if post_date_str:
                        try:
                            post_year = int(post_date_str[:4])
                            # 요청한 학년도와 게시 연도가 일치하면 포함
                            if post_year == requested_year or (post_year == requested_year + 1 and current_month <= 2):
                                filtered_docs.append(doc)
                        except:
                            filtered_docs.append(doc)
            
            if filtered_docs:
                retrieved_docs = filtered_docs[:self.TOP_K]
                print(f"🔍 학년도 필터링: {requested_year}학년도 관련 {len(retrieved_docs)}건만 선택")
        
        # 검색된 문서의 board_type 분석하여 답변 형식 결정
        board_types = [doc['metadata'].get('board_type', '전체공지') for doc in retrieved_docs]
        dominant_type = max(set(board_types), key=board_types.count) if board_types else '전체공지'
        
        # 동아리 질문 감지
        query_lower = user_query.lower()
        if '동아리' in query_lower and '소프트웨어' in query_lower:
            dominant_type = '동아리'
            print(f"🎯 동아리 질문 감지! dominant_type = {dominant_type}")
        
        # 졸업요건 질문 감지
        if '졸업요건' in query_lower or '졸업 요건' in query_lower:
            dominant_type = '졸업요건'
            print(f"🎯 졸업요건 질문 감지! dominant_type = {dominant_type}")
        
        # 기숙사 연락처 질문 감지
        dorm_names = ['양진재', '양성재', '양현재', '개성재', '계영원']
        has_dorm = any(name in query_lower for name in dorm_names) or '기숙사' in query_lower or '생활관' in query_lower
        has_contact = '연락처' in query_lower or '전화' in query_lower or '번호' in query_lower
        
        if has_dorm and has_contact:
            dominant_type = '기숙사연락처'
            print(f"🎯 기숙사 연락처 질문 감지! dominant_type = {dominant_type}")
        
        # 카테고리별 답변 형식 지정
        if dominant_type == '기숙사연락처':
            format_instruction = """
[답변 형식 - 기숙사 연락처]

각 기숙사의 전화번호를 다음 형식으로 나열하세요:

- **기숙사명: ☏ 전화번호**

예시:
- **양진재: ☏ 043-249-1870**

마지막에 URL만 추가:
**URL**: [문서의 source_url]

**중요:** 
- 각 기숙사를 별도 줄로 나열하세요
- "이 정보는...", "자세한 내용은..." 같은 추가 설명 금지
- 출처 정보 중복 금지
"""
        elif dominant_type == '졸업요건':
            # 학번 추출
            import re
            year_match = re.search(r'(21|22|23|24|25)학번', user_query)
            year_str = year_match.group(0) if year_match else "해당 학번"
            
            # 문서에서 URL 추출
            source_urls = list(set([doc['metadata'].get('source_url', '') for doc in retrieved_docs if doc['metadata'].get('source_url')]))
            url_str = source_urls[0] if source_urls else "https://software.cbnu.ac.kr/sub0501"
            
            format_instruction = f"""
[답변 형식 - 졸업요건]

{year_str} 소프트웨어학부 졸업요건을 안내드립니다.

**졸업이수기준학점:**
문서에서 "학과(부)별 졸업이수기준학점" 표를 찾아 다음 정보를 정확히 추출하세요:

1. 졸업학점: [문서에서 찾은 총 졸업학점]
2. 교양과정: [문서에서 찾은 교양 학점]
3. 전공과정:
   - 전공필수: [문서에서 찾은 전공필수 학점]
   - 전공선택: [문서에서 찾은 전공선택 학점]
   - 전공 합계: [문서에서 찾은 전공 소계]
4. 일반선택: [문서에서 찾은 일반선택 학점]

**자세한 교육과정 및 이수모형은 아래 링크를 참고하세요:**
{url_str}

**중요:** 
- 문서의 표에서 정확한 숫자를 찾아 기재하세요
- 교육과정 상세 내용(과목 목록 등)은 URL 안내만 하세요
- 문서에 없는 내용은 절대 만들지 마세요
"""
        elif dominant_type == '동아리':
            format_instruction = """
[답변 형식 - 소프트웨어학부 동아리]
소프트웨어학부 동아리를 안내드립니다.

**중요 지시사항:**
1. 검색된 문서에 나열된 **모든 동아리**를 빠짐없이 답변에 포함하세요
2. 각 동아리의 정보를 문서에서 그대로 복사하세요
3. 절대로 임의로 동아리를 만들거나 내용을 추가하지 마세요
4. 문서에 없는 동아리는 절대 언급하지 마세요

**답변 형식:**

소프트웨어학부 동아리 목록:

[문서에 나온 각 동아리를 다음 형식으로 나열]

1. **동아리명**
   - 동아리장: [문서 내용]
   - 지도교수: [문서 내용]
   - 위치: [문서 내용]
   - 동아리 소개: [문서 내용]
   - 주요활동: [문서 내용]

2. **동아리명**
   ...

**출처:** https://software.cbnu.ac.kr/sub040301
"""
        elif dominant_type.startswith('소프트웨어학부'):
            # 소프트웨어학부 전용 형식
            if '정적정보' in dominant_type:
                format_instruction = """
[답변 형식 - 소프트웨어학부 정보]
질문하신 내용에 대해 안내드립니다.

[핵심 내용]
(검색된 정보를 바탕으로 명확하게 설명)

자세한 정보는 소프트웨어학부 홈페이지를 참고해주세요.
https://software.cbnu.ac.kr/
"""
            else:
                format_instruction = """
[답변 형식 - 소프트웨어학부 공지]
소프트웨어학부 관련 공지사항을 안내드립니다.

**[공지 제목]**
- 일시: (있는 경우)
- 대상: (있는 경우)
- 신청/접수: (있는 경우)
- 주요 내용: (상세 정보)
- URL: (검색된 정보의 source_url 필수 포함)

이 정보는 소프트웨어학부 공지사항을 통해 확인된 내용입니다.
"""
        elif dominant_type == '학사일정':
            format_instruction = """
[답변 형식 - 학사일정]
2025학년도 2학기 [일정명]은 **YYYY년 MM월 DD일(요일)부터 YYYY년 MM월 DD일(요일)까지**입니다.

**세부 일정:**
- **[일정명]:** YYYY년 MM월 DD일(요일) ~ YYYY년 MM월 DD일(요일)

**참고 자료:**
- **출처:** [공지 제목] / URL: [검색된 정보의 source_url 필수 포함]

[추가 안내 메시지가 있다면 포함]
"""
        elif dominant_type == '기숙사':
            # 기숙사 내에서도 연락처/위치/식단/공지 구분
            query_lower = user_query.lower()
            if any(kw in query_lower for kw in ['연락처', '전화', '번호', '문의']):
                format_instruction = """
[답변 형식 - 기숙사 연락처]
기숙사 연락처는 다음과 같습니다:

- 본관(개성재, 계영원): 043-261-2926
- 양성재: 043-261-3675
- 양진재: 043-249-1870
- 양현재: 043-261-2932

자세한 정보는 충북대학교 학생생활관 홈페이지를 참고해주세요.
https://dorm.chungbuk.ac.kr/home/main.php
"""
            elif any(kw in query_lower for kw in ['위치', '장소', '어디']):
                format_instruction = """
[답변 형식 - 기숙사 위치]
충북대학교 학생생활관은 캠퍼스 내에 위치해 있습니다.

자세한 위치 정보는 충북대학교 학생생활관 홈페이지를 참고해주세요.
https://dorm.chungbuk.ac.kr/home/main.php
"""
            elif any(kw in query_lower for kw in ['식단', '메뉴', '밥']):
                # 본관/양성재/양진재 구분
                building = "본관"
                if '양성재' in query_lower:
                    building = "양성재"
                elif '양진재' in query_lower:
                    building = "양진재"
                elif '본관' in query_lower:
                    building = "본관"
                
                # 검색된 문서에서 해당 건물의 실제 URL 찾기
                menu_url = "https://dorm.chungbuk.ac.kr/home/sub.php?menukey=20041"
                for doc in retrieved_docs:
                    if building in doc['metadata'].get('title', '') and '식단표' in doc['metadata'].get('title', ''):
                        menu_url = doc['metadata'].get('source_url', menu_url)
                        break
                
                # 이번 주 날짜 계산
                week_dates = self._get_week_dates_map()
                
                # 건물별 요일 구성
                if building in ['양성재', '양진재']:
                    example_day = f"""
**일요일 ({week_dates['일']})**

* **아침**: 잡곡밥 또는 쌀밥, 소고기뭇국 (호주산 우육), 가지돈민찌볶음 (국산 돈육), 잡채어묵메추리알매운조림, 배추겉절이, 우유 또는 두유 또는 주스 (930kcal/22g)
* **점심**: [문서의 일요일 점심 메뉴를 위 형식처럼 그대로 복사]
* **저녁**: [문서의 일요일 저녁 메뉴를 위 형식처럼 그대로 복사]

**월요일 ({week_dates['월']})**

* **아침**: [문서의 월요일 아침 메뉴를 위 형식처럼 그대로 복사]
* **점심**: [문서의 월요일 점심 메뉴를 위 형식처럼 그대로 복사]
* **저녁**: [문서의 월요일 저녁 메뉴를 위 형식처럼 그대로 복사]

(화요일~토요일까지 같은 방식으로 계속)
"""
                else:  # 본관
                    example_day = f"""
**월요일 ({week_dates['월']})**

* **아침**: 잡곡밥 또는 쌀밥, 소고기뭇국 (호주산 우육), 가지돈민찌볶음 (국산 돈육), 잡채어묵메추리알매운조림, 배추겉절이, 우유 또는 두유 또는 주스 (930kcal/22g)
* **점심**: [문서의 월요일 점심 메뉴를 위 형식처럼 그대로 복사]
* **저녁**: [문서의 월요일 저녁 메뉴를 위 형식처럼 그대로 복사]

**화요일 ({week_dates['화']})**

* **아침**: [문서의 화요일 아침 메뉴를 위 형식처럼 그대로 복사]
* **점심**: [문서의 화요일 점심 메뉴를 위 형식처럼 그대로 복사]
* **저녁**: [문서의 화요일 저녁 메뉴를 위 형식처럼 그대로 복사]

(수요일~금요일까지 같은 방식으로 계속)
"""
                
                format_instruction = f"""
[답변 형식 - 기숙사 식단]
**절대 규칙: 아래 예시 형식을 정확히 따라 작성하세요**

## 2025학년도 {building} 식단 안내

{example_day}

**참고**: 위 식단은 예시이며, 실제 제공 메뉴 및 영양 정보는 변경될 수 있습니다. 정확한 정보는 {building} 식당 공지사항을 참조하십시오.

**URL**: {menu_url}

**필수 준수사항:**
1. 각 요일 옆에 반드시 날짜 표시: **월요일 ({week_dates['월']})** 형식
2. 인사말 절대 금지
3. 메뉴는 문서에서 그대로 복사 (요약 금지)
4. 본관: 월~금, 양성재/양진재: 일~토 (일요일부터 시작)
5. **반드시 마지막에 URL 포함**: **URL**: {menu_url}
"""
            else:  # 기숙사 공지사항
                format_instruction = """
[답변 형식 - 기숙사 공지]
[핵심 내용 요약]

일시: (있는 경우)
장소: (있는 경우)
대상: (있는 경우)
주요 내용: (상세 정보)

이 정보는 충북대학교 학생생활관 공지사항을 통해 확인된 내용입니다.
"""
        else:  # 전체공지
            format_instruction = """
[답변 형식 - 전체공지]
안녕하세요! 관련 공지사항을 알려드리겠습니다.

### [카테고리명]
1. **[공지 제목]**
   - **기간**: YYYY년 MM월 DD일 ~ MM월 DD일
   - **대상**: (해당자)
   - **방법**: (신청/접수 방법)
   - **참고사항**: (추가 정보)
   - **URL**: https://www.cbnu.ac.kr/... (검색된 정보의 source_url을 반드시 포함)

**중요**: 각 공지사항마다 반드시 URL 항목을 포함하고, 검색된 정보의 실제 source_url을 정확히 기재하세요.
"""
        
        # 일정 추가 요청 감지
        event_add_keywords = ['일정 추가', '일정추가', '캘린더에 추가', '캘린더 추가', '일정 등록', '일정등록', '추가해줘', '추가해주세요', '넣어줘', '등록해줘']
        pronoun_keywords = ['이 일정', '그 일정', '해당 일정', '위 일정']
        question_keywords = ['언제', '몇시', '며칠', '무슨 날', '알려줘', '알려주세요', '뭐야', '뭐지']
        
        has_pronoun = any(keyword in user_query for keyword in pronoun_keywords)
        
        is_event_add_request = (
            (any(keyword in user_query for keyword in event_add_keywords) and
             not any(keyword in user_query for keyword in question_keywords)) or
            (has_pronoun and any(kw in user_query for kw in ['추가', '등록', '넣어']))
        )
        
        # 일정 추가 요청이면 RAG 검색 없이 바로 처리
        if is_event_add_request:
            print("🎯 일정 추가 요청 감지 - RAG 검색 건너뛰고 바로 처리")
            
            if has_pronoun:
                # 대명사 기반: 이전 대화에서 일정 찾기
                chat_context = ""
                if recent_chats:
                    chat_context = "\n\n[이전 대화 맥락]\n" + "\n".join([
                        f"{chat.role}: {chat.content}"
                        for chat in reversed(list(recent_chats))
                    ])
                
                simple_prompt = f"""
오늘 날짜: {current_date.strftime('%Y년 %m월 %d일')}

{chat_context}

사용자 요청: {user_query}

위 이전 대화에서 언급된 일정 정보를 찾아 다음 형식으로만 답변하세요:

일정이 추가되었습니다.

[EVENT_ADD]{{"title": "일정제목", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "description": "설명"}}[/EVENT_ADD]

예시:
이전 대화: "2025학년도 1학기 개강일은 2025년 3월 3일(월)입니다."
현재 요청: "이 일정 추가해줘"
답변: 일정이 추가되었습니다.

[EVENT_ADD]{{"title": "개강일", "start_date": "2025-03-03", "end_date": "2025-03-03", "description": "2025학년도 1학기 개강일"}}[/EVENT_ADD]

중요: 이전 대화에서 날짜와 일정명을 찾아 태그를 생성하세요.
"""
            else:
                # 직접 명시: 질문에서 일정 추출
                simple_prompt = f"""
오늘 날짜: {current_date.strftime('%Y년 %m월 %d일')}

사용자 요청: {user_query}

위 요청에서 일정 정보를 추출하여 다음 형식으로만 답변하세요:

일정이 추가되었습니다.

[EVENT_ADD]{{"title": "일정제목", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "description": "일정제목"}}[/EVENT_ADD]

예시:
- "12월 19일에 교양 기말고사 일정 추가해줘" 
  → 일정이 추가되었습니다.
  
  [EVENT_ADD]{{"title": "교양 기말고사", "start_date": "2025-12-19", "end_date": "2025-12-19", "description": "교양 기말고사"}}[/EVENT_ADD]

중요: 
- 날짜는 YYYY-MM-DD 형식으로 변환하세요
- 연도가 없으면 2025년으로 가정하세요
- 다른 설명 없이 위 형식만 출력하세요
"""
            
            try:
                response = requests.post(
                    self.ollama_url,
                    json={
                        "model": self.ollama_model,
                        "prompt": simple_prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.0,
                        }
                    },
                    timeout=60
                )
                response.raise_for_status()
                answer = response.json().get("response", "일정 추가 요청을 처리할 수 없습니다.")
                
                return {
                    "answer": answer.strip(),
                    "sources": [],
                    "source_url": None
                }
            except Exception as e:
                print(f"❌ Ollama 요청 실패: {e}")
                return {
                    "answer": "일정 추가 요청을 처리하는 중 오류가 발생했습니다.",
                    "sources": [],
                    "source_url": None
                }
        
        event_add_instruction = ""
        if is_event_add_request:
            if has_pronoun:
                event_add_instruction = """

**[!!!긴급 - 일정 추가 요청!!!]**
사용자가 "이 일정", "그 일정" 등으로 이전 대화의 일정을 추가하려고 합니다.

**절대 규칙:**
1. 이전 대화 맥락에서 날짜와 일정명을 찾으세요
2. 다른 정보는 무시하고 오직 일정 추가만 처리하세요
3. 반드시 답변 끝에 다음 태그를 추가하세요:

[EVENT_ADD]{"title": "일정제목", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "description": "설명"}[/EVENT_ADD]

**예시:**
이전 대화: "2025학년도 1학기 개강일은 2025년 3월 3일(월)입니다."
현재 요청: "이 일정 추가해줘"
답변: 개강일 일정을 추가했습니다.

[EVENT_ADD]{"title": "개강일", "start_date": "2025-03-03", "end_date": "2025-03-03", "description": "2025학년도 1학기 개강일"}[/EVENT_ADD]

**이 태그 없이는 절대 답변하지 마세요!**
"""
            else:
                event_add_instruction = """

[중요 - 일정 추가 요청 감지됨!]
사용자가 일정 추가를 요청했습니다. 반드시 답변 마지막에 다음 형식을 포함하세요:

[EVENT_ADD]{"title": "일정제목", "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD", "description": "설명"}[/EVENT_ADD]

예시:
- "12월 20일에 기말고사 일정 추가해줘" → [EVENT_ADD]{"title": "기말고사", "start_date": "2025-12-20", "end_date": "2025-12-20", "description": "기말고사"}[/EVENT_ADD]

반드시 이 형식을 답변 끝에 추가하세요!
"""
        
        full_prompt = f"""
{SYSTEM_PROMPT}

[현재 시점 정보 - 매우 중요!]
- 오늘 날짜: {current_date.strftime('%Y년 %m월 %d일')}
- 현재 학기: {current_semester} ({semester_period})
- 사용자 요청 학년도: {requested_year}학년도

[학년도 판단 규칙 - 절대 준수!]
- 사용자가 "{requested_year}학년도"를 물었습니다.
- 검색된 문서 중 "{requested_year}학년도" 정보만 사용하세요.
- 다른 학년도 정보는 절대 포함하지 마세요.
- 답변 시 반드시 "{requested_year}학년도"를 명시하세요.

{format_instruction}
{event_add_instruction}

**[식단 답변 시 절대 규칙]**
식단 질문인 경우 반드시 아래 형식을 정확히 따르세요:
- 각 요일 옆에 괄호로 날짜 표시 필수: **월요일 (2025-12-09)**
- 날짜 없이 **월요일**만 쓰면 안 됩니다
- 인사말("안녕하세요", "여러분") 절대 금지

{chat_context}

[검색된 정보]
{context_text}

[사용자 질문]
{user_query}

[지시사항]
위 [검색된 정보]를 바탕으로 [사용자 질문]에 대해 **한국어**로 친절하게 답변하세요. 
**반드시 {requested_year}학년도 정보만 답변하세요. 다른 학년도 정보는 언급하지 마세요.**
위에 제시된 [답변 형식]을 따라 답변해주세요.

**중요**: 각 공지사항마다 반드시 "URL:" 항목을 포함하고, [검색된 정보]에 제공된 실제 URL을 정확히 복사하여 기재하세요.
예시: - **URL**: https://www.cbnu.ac.kr/www/selectBbsNttView.do?key=813&bbsNo=8&nttNo=158484

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
            
            # 후처리: 기숙사 연락처/위치 질문에 메인 사이트 링크 추가
            query_lower = user_query.lower()
            if dominant_type == '기숙사':
                if any(kw in query_lower for kw in ['연락처', '전화', '번호', '문의']):
                    if 'dorm.chungbuk.ac.kr/home/main.php' not in answer:
                        answer += "\n\n자세한 정보는 충북대학교 학생생활관 홈페이지를 참고해주세요.\nhttps://dorm.chungbuk.ac.kr/home/main.php"
                elif any(kw in query_lower for kw in ['위치', '장소', '어디']):
                    if 'dorm.chungbuk.ac.kr/home/main.php' not in answer:
                        answer += "\n\n자세한 위치 정보는 충북대학교 학생생활관 홈페이지를 참고해주세요.\nhttps://dorm.chungbuk.ac.kr/home/main.php"

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