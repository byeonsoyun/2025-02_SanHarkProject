import sys
import os
import time

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings

# RAGService 클래스 임포트
# NOTE: Django 환경이 이미 설정되어 있으므로, 상대 경로 임포트가 가능합니다.
try:
    from chat.services import RAGService 
except ImportError as e:
    # RAGService 임포트 실패는 치명적이므로 오류를 보고합니다.
    print(f"❌ RAGService 임포트 실패: {e}")
    sys.exit(1)


class Command(BaseCommand):
    """
    RAG 파이프라인의 전체 업데이트를 순서대로 수행하는 Django 관리 명령어입니다.
    순서: 1. 데이터 크롤링 -> 2. 벡터 인덱스 초기화 -> 3. 벡터 인덱싱
    
    사용법: python manage.py run_rag_update
    """
    help = 'Runs the complete RAG update pipeline: Crawling, clearing index, and re-indexing.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("========================================"))
        self.stdout.write(self.style.MIGRATE_HEADING("🚀 RAG 전체 업데이트 파이프라인 시작"))
        self.stdout.write(self.style.MIGRATE_HEADING("========================================"))

        # --- 단계 1: 데이터 크롤링 (원본 데이터 최신화) ---
        self.stdout.write(self.style.NOTICE("\n[단계 1/3]: Scrapy 크롤러 실행 (원본 데이터 수집)"))
        try:
            # 기존에 정의된 Django 관리 명령어 'run_crawler' 호출
            # 이는 'chat/management/commands/run_crawler.py'에 정의되어 있어야 합니다.
            call_command('run_crawler')
            self.stdout.write(self.style.SUCCESS("✅ 크롤링 성공. ChbNotice 테이블이 최신 데이터로 업데이트되었습니다."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ 크롤링 실패: run_crawler 명령어 실행 중 오류가 발생했습니다: {e}"))
            return # 실패 시 인덱싱 중단

        # --- 단계 2: RAG 인덱스 초기화 ---
        self.stdout.write(self.style.NOTICE("\n[단계 2/3]: RAG 벡터 인덱스 초기화 (NoticeRagIndex 테이블 TRUNCATE)"))
        if RAGService.clear_rag_index():
            self.stdout.write(self.style.SUCCESS("✅ 벡터 인덱스 초기화 성공."))
        else:
            self.stdout.write(self.style.ERROR("❌ 벡터 인덱스 초기화 실패. DB 연결 상태를 확인하십시오."))
            return # 실패 시 인덱싱 중단
            
        # --- 단계 3: 벡터 인덱싱 (임베딩 및 저장) ---
        self.stdout.write(self.style.NOTICE("\n[단계 3/3]: 벡터 인덱싱 실행 (청킹, 임베딩 및 저장)"))
        
        try:
            rag_service = RAGService()
            if rag_service.embedder is not None:
                total_indexed = rag_service.embed_and_index_documents()
                self.stdout.write(self.style.SUCCESS(f"✅ 벡터 인덱싱 성공. 총 {total_indexed}개의 청크가 DB에 저장되었습니다."))
            else:
                self.stdout.write(self.style.ERROR("❌ 인덱싱 실패: 임베딩 모델 로드 오류."))
                return # 실패 시 인덱싱 중단
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ 인덱싱 중 치명적인 오류 발생: {e}"))
            return # 실패 시 인덱싱 중단

        self.stdout.write(self.style.MIGRATE_HEADING("\n========================================"))
        self.stdout.write(self.style.MIGRATE_HEADING("🎉 RAG 전체 업데이트 파이프라인 완료"))
        self.stdout.write(self.style.MIGRATE_HEADING("========================================"))