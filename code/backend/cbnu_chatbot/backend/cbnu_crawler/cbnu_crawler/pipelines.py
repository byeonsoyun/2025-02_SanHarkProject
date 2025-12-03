import os
import django
import sys 
from scrapy.exceptions import DropItem
from asgiref.sync import sync_to_async
from datetime import datetime

# 🌟 1. 현재 파일의 위치를 기준으로 Django 프로젝트의 루트 디렉토리 (manage.py가 있는 'backend' 폴더)를 찾습니다.
DJANGO_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# 🌟 2. Python의 모듈 검색 경로에 Django 프로젝트 루트를 추가합니다. (필수)
if DJANGO_PROJECT_ROOT not in sys.path:
    sys.path.insert(0, DJANGO_PROJECT_ROOT)

# 🌟 3. Django 환경 설정 로드. 실제 설정 파일이 있는 폴더 이름은 'backend'입니다.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# 🌟 4. 'chat' 앱에서 ChbNotice 모델을 가져옵니다.
# ChbNotice 모델이 'notice_id' 필드를 Unique/Primary Key로 가지고 있다고 가정합니다.
from chat.models import ChbNotice

class DjangoPipeline:
    def process_item(self, item, spider):
        # 비동기 환경인 Scrapy에서 Django ORM을 안전하게 사용하기 위해 sync_to_async 사용
        return sync_to_async(self._save_item, thread_sensitive=True)(item, spider)

    def _save_item(self, item, spider):
        """
        실제로 Django ORM을 사용하여 데이터를 저장하는 동기(Synchronous) 함수
        """
        pk_key = item.get('notice_id') # Item의 Primary Key 사용
        actual_post_date = item.get('post_date') # 스파이더에서 전달한 실제 날짜 객체 사용
        
        if not pk_key or not actual_post_date:
            spider.logger.error(f"❌ 필수 필드(notice_id: {pk_key}, post_date: {actual_post_date}) 누락. 건너뜀.")
            raise DropItem("Missing essential fields.")

        try:
            # update_or_create는 notice_id를 기준으로 레코드를 찾습니다.
            # - 레코드가 없으면: defaults와 post_date=... 를 사용하여 생성합니다.
            # - 레코드가 있으면: defaults 내부의 필드만 업데이트하고, post_date는 업데이트하지 않고 보존합니다.
            obj, created = ChbNotice.objects.update_or_create( 
                # 룩업 조건: notice_id (Django 모델의 unique key 필드)
                notice_id=pk_key, 
                
                # 생성 시에만 적용: post_date는 생성 시에만 설정하고 업데이트 시에는 무시합니다.
                post_date=actual_post_date, # 👈 스파이더에서 추출한 정확한 날짜 객체를 사용합니다.
                
                defaults={
                    'title': item['title'],
                    'content': item['content'],
                    'source_url': item['url'], # Item 필드 'url'을 모델 필드 'source_url'에 매핑
                    'board_type': item['board_type'],
                }
            )

            if created:
                spider.logger.debug(f"✅ DB 저장 성공 (새로 생성): {item['title'][:20]}... (PK: {pk_key}, Date: {actual_post_date})")
            else:
                # obj.post_date는 데이터베이스에 저장된 기존 날짜입니다.
                spider.logger.debug(f"✅ DB 업데이트 성공 (기존 레코드): {item['title'][:20]}... (PK: {pk_key}, Date preserved: {obj.post_date})")

            return item
        except Exception as e:
            spider.logger.error(f"❌ DB 저장 오류 (PK: {pk_key}) - 에러: {e}")
            raise DropItem(f"Database error on item {pk_key}: {e}")