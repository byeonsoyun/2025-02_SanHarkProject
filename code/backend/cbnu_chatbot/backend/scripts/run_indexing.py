import os
import django
import sys
from pathlib import Path 

# 현재 파일의 경로 (backend/scripts/run_indexing.py)
CURRENT_FILE_PATH = Path(__file__).resolve()

# Django 프로젝트의 루트 디렉토리 (backend/manage.py가 있는 폴더)
DJANGO_PROJECT_ROOT = CURRENT_FILE_PATH.parent.parent 

# --- FIX: backend 폴더를 sys.path에 추가하여 'backend.settings'를 찾을 수 있도록 함 ---
if str(DJANGO_PROJECT_ROOT) not in sys.path:
    sys.path.append(str(DJANGO_PROJECT_ROOT))
# -------------------------------------------------------------------------------------

# 프로젝트의 설정을 로드하기 위해 Django 환경 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup() 

# RAGService 클래스 임포트
try:
    from chat.services import RAGService 
except ImportError as e:
    print(f"❌ RAGService 임포트 실패: {e}")
    print("chat.services 파일이 존재하는지, 경로가 올바른지 확인해 주세요.")
    sys.exit(1)

# --- 주의사항: 이 스크립트 실행 전에 크롤링을 먼저 수행해야 합니다. ---
# 실행 명령어: python manage.py run_crawler


if __name__ == "__main__":
    print("========================================")
    print("🏗️ RAG 벡터 인덱싱 (pgvector) 시작")
    print("========================================")

    # 1. [변경됨] RAG 인덱스 초기화 (기존 DB 데이터 삭제)
    print("\n[단계 1/2]: 기존 RAG 인덱스 데이터 초기화 시도 (NoticeRagIndex 테이블 TRUNCATE)")
    try:
        # RAGService 내부에 NoticeRagIndex.objects.all().delete() 로직이 필요합니다.
        RAGService.clear_rag_index()
        print("⚠️ NoticeRagIndex 테이블의 기존 데이터가 삭제되었습니다.")
    except Exception as e:
        print(f"❌ DB 인덱스 초기화 실패: {e}")
        sys.exit(1)
        
    # 2. RAG 서비스 초기화 및 인덱싱 실행
    print("\n[단계 2/2]: 임베딩 및 pgvector DB에 청크 저장")
    
    rag_service = RAGService()
    
    # 모델 로드 확인
    if rag_service.embedder is not None:
        # 인덱싱 함수 호출 (ChbNotice에서 데이터를 읽어 벡터 DB에 저장)
        chunk_count = rag_service.embed_and_index_documents()
        
        if chunk_count > 0:
            print("\n✅ RAG 벡터 인덱싱 성공! 총 {}개의 청크가 pgvector DB에 저장되었습니다.".format(chunk_count))
            # 쿼리 성능 최적화를 위한 HNSW 인덱스 생성 로직이 RAGService 내부에 필요합니다.
        else:
            print("\n❌ RAG 벡터 인덱싱 실패! ChbNotice 테이블을 확인하거나 오류 로그를 참조하십시오.")
    else:
        print("❌ 인덱싱 실패: 임베딩 모델 로드 오류로 인해 작업을 건너뜁니다.")
            
    print("========================================")
    print("✅ RAG 인덱싱 프로세스 완료")
    print("========================================")