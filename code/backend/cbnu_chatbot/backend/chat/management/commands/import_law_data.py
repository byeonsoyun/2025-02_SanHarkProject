from django.core.management.base import BaseCommand
from chat.models import LawDocument 
from django.db import transaction
from chat.crawler_modules.law_api_config import API_CONFIG 
from typing import List, Any
import time

class Command(BaseCommand):
    help = 'API 설정 파일을 기반으로 모든 법률 데이터를 수집하고 DB에 업데이트합니다.'

    def _upsert_data(self, all_collected_data: List[Any], data_type: str):
        """수집된 데이터를 LawDocument 테이블에 업데이트/생성합니다."""
        total_created = 0
        total_updated = 0
        
        if not all_collected_data:
            self.stdout.write(self.style.NOTICE(f"API로부터 수집된 {data_type} 데이터가 없습니다."))
            return

        # Pydantic 모델을 딕셔너리로 변환
        # LawData 모델의 model_dump() 사용
        data_to_upsert = [d.model_dump() for d in all_collected_data]

        self.stdout.write(f"🔍 총 {len(data_to_upsert)}건의 {data_type} 데이터를 DB에 반영합니다.")

        with transaction.atomic():
            for item in data_to_upsert:
                doc_id = item.pop('document_id')
                
                # LawDocument.objects.update_or_create를 사용하여 데이터 반영
                doc, created = LawDocument.objects.update_or_create(
                    document_id=doc_id,
                    defaults={
                        'doc_type': item['doc_type'],
                        'title': item['title'],
                        'content': item['content'],
                        'source_url': item['source_url'],
                    }
                )
                if created:
                    total_created += 1
                else:
                    total_updated += 1
        
        self.stdout.write(self.style.SUCCESS(
            f"✅ [업데이트 완료] {data_type} 테이블 업데이트 성공. 생성: {total_created}건, 업데이트: {total_updated}건."
        ))

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🌟 [API 크롤링 시작] LawDocument 업데이트 프로세스 시작."))
        
        # 🚨 API 설정 파일을 순회하며 자동 실행 🚨
        for config in API_CONFIG:
            api_name = config["name"]
            collector_func = config["collector_function"]
            
            self.stdout.write(self.style.HTTP_INFO(f"\n--- [시작] {api_name} 데이터 수집 ---"))
            
            try:
                # 데이터 수집 함수 호출
                start_time = time.time()
                collected_data = collector_func() 
                end_time = time.time()
                
                self.stdout.write(self.style.NOTICE(f"⏳ {api_name} 수집 시간: {end_time - start_time:.2f}초."))
                
                # 수집된 데이터를 DB에 저장/업데이트
                self._upsert_data(collected_data, api_name)
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ [크롤링 실패] {api_name} 오류 발생: {e}"))
                self.stdout.write(self.style.WARNING("--- 다음 API로 진행합니다. ---"))
        
        self.stdout.write(self.style.SUCCESS("\n✨ 모든 법률 데이터 수집 프로세스 완료."))
