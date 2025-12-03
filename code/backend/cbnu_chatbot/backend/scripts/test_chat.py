import os
import django
import sys
from pathlib import Path

# 현재 파일의 경로 (backend/scripts/test_chat.py)
CURRENT_FILE_PATH = Path(__file__).resolve()

# Django 프로젝트의 루트 디렉토리 (backend/manage.py가 있는 폴더)
# CURRENT_FILE_PATH.parent.parent -> backend 폴더
DJANGO_PROJECT_ROOT = CURRENT_FILE_PATH.parent.parent 

# --- FIX: backend 폴더를 sys.path에 추가하여 'backend.settings'를 찾을 수 있도록 함 ---
# 이 스크립트가 'project' 디렉토리에서 실행되므로, 'backend' 폴더를 직접 추가해야 합니다.
if str(DJANGO_PROJECT_ROOT) not in sys.path:
    sys.path.append(str(DJANGO_PROJECT_ROOT))
# -------------------------------------------------------------------------------------

# 프로젝트의 설정을 로드하기 위해 Django 환경 설정
# settings 파일의 위치가 `backend.backend.settings`가 아니라 `backend.settings`인 경우
# 프로젝트 루트 폴더(`backend` 폴더)를 sys.path에 추가해야 합니다.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup() 

# RAGService 클래스 임포트
try:
    # DJANGO_PROJECT_ROOT가 sys.path에 추가되었으므로,
    # 'chat' 앱을 직접 임포트할 수 있습니다.
    from chat.services import RAGService 
except ImportError as e:
    print(f"❌ RAGService 임포트 실패: {e}")
    print(f"현재 sys.path: {sys.path}")
    print("chat.services 파일이 존재하는지, 경로가 올바른지 확인해 주세요.")
    sys.exit(1)


if __name__ == "__main__":
    
    # settings.py의 FAISS_DB_PATH를 로드하기 위해 RAGService 인스턴스 생성 시도
    rag_service = RAGService()
    
    if rag_service.embedder is None:
        print("❌ RAG 서비스 초기화 실패: 임베딩 모델이 로드되지 않았습니다.")
        sys.exit(1)
        
    # 테스트할 질문 목록 (충북대 공지사항 관련)
    test_queries = [
        "이번 학기 등록금 납부는 언제까지 해야 하나요?",
        "장학금 신청 자격에 대해 알려주세요.",
        "도서관 휴관일이 변경되었나요?",
        "기숙사 신청 방법 좀 알려줘"
    ]
    
    for query in test_queries:
        print("="*60)
        print(f"User Query: {query}")
        print("="*60)
        
        # 챗봇 답변 생성 요청
        result = rag_service.generate_rag_response(query) 
        
        print("\n--- 🤖 최종 답변 ---")
        print(result['answer'])
        
        print("\n--- 📄 검색된 출처 정보 ---")
        if result['sources']:
            # 중복 제거를 위해 notice_id 기준으로 필터링
            unique_sources = {}
            for source in result['sources']:
                # 공지사항 고유 ID를 키로 사용하여 중복 제거
                if source['notice_id'] not in unique_sources:
                    unique_sources[source['notice_id']] = source

            for source in unique_sources.values():
                print(f"- 제목: {source.get('title', '제목 없음')}")
                print(f"  URL: {source.get('url', '링크 없음')}") 
                print(f"  게시일: {source.get('post_date', 'N/A')}")
                print(f"  게시판: {source.get('board_type', 'N/A')}")
        else:
            print("검색된 공지사항 근거가 없습니다.")
        print("\n" + "="*60 + "\n")