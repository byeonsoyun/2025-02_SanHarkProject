import logging
from django.core.management.base import BaseCommand
from chat.services import RAGService 
# RAGService가 이제 pgvector 기반으로 수정되어야 합니다.

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "ChbNotice 테이블의 데이터를 기반으로 RAG 벡터 인덱스(pgvector)를 생성하고 저장합니다."

    def handle(self, *args, **options):
        self.stdout.write("=" * 40)
        self.stdout.write("🏗️ RAG 벡터 인덱싱 (pgvector) 시작")
        self.stdout.write("=" * 40)

        # 1. RAGService 인스턴스 생성 및 모델 로드
        try:
            rag_service = RAGService()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ RAGService 초기화 실패: {e}"))
            return

        # 2. [변경됨] 기존 pgvector 인덱스(DB 데이터) 초기화 (선택 사항이지만 안전을 위해 수행)
        self.stdout.write("\n[단계 1/2]: 기존 RAG 인덱스 데이터 초기화 시도 (NoticeRagIndex 테이블 TRUNCATE)")
        # RAGService 내부에 NoticeRagIndex.objects.all().delete() 또는 TRUNCATE 로직이 필요합니다.
        try:
            RAGService.clear_rag_index() # 이 함수는 이제 DB 데이터를 지우도록 수정되어야 합니다.
            self.stdout.write(self.style.WARNING("⚠️ NoticeRagIndex 테이블의 기존 데이터가 삭제되었습니다."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ DB 인덱스 초기화에 실패하여 인덱싱을 중단합니다: {e}"))
            return

        # 3. [변경됨] 문서 임베딩 및 pgvector DB에 청크 저장
        self.stdout.write("\n[단계 2/2]: 임베딩 및 pgvector DB에 청크 저장")
        try:
            # embed_and_index_documents 함수가 이제 DB에 데이터를 삽입합니다.
            indexed_count = rag_service.embed_and_index_documents()
            
            if indexed_count > 0:
                # 쿼리 성능 최적화를 위한 HNSW 인덱스 생성 로직이 RAGService 내부에 필요합니다.
                self.stdout.write(self.style.SUCCESS(f"\n✅ RAG 벡터 인덱싱 성공! 총 {indexed_count}개의 청크가 pgvector DB에 저장되었습니다."))
            else:
                self.stdout.write(self.style.WARNING("\n⚠️ RAG 벡터 인덱싱 완료. 인덱스에 추가된 청크가 없습니다. (원본 데이터 ChbNotice 확인 필요)"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ RAG 벡터 인덱싱 중 치명적인 오류 발생: {e}"))
            logger.exception("RAG 벡터 인덱싱 중 예외 발생")

        self.stdout.write("=" * 40)
        self.stdout.write("✅ RAG 인덱싱 프로세스 완료")
        self.stdout.write("=" * 40)