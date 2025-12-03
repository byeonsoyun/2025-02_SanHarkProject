#cbnu_crawler 실행 Django 명령
#python manage.py run_crawler 명령으로 크롤링 할 수 있음
#chat/management/commands/run_crawler.py

import os
from django.core.management.base import BaseCommand
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
# 🚨 수정된 부분: Scrapy 프로젝트가 중첩된 디렉토리 구조(cbnu_crawler/cbnu_crawler)를 가지므로
# import 경로에 패키지 이름을 두 번 명시해야 합니다.
from cbnu_crawler.cbnu_crawler.spiders.cbnu_notice_spider import CbnuNoticeSpider

class Command(BaseCommand):
    """
    Django 관리 명령어로 Scrapy 스파이더를 실행합니다.
    사용법: python manage.py run_crawler
    """
    help = 'Runs the cbnu_notice Scrapy spider to crawl and update the notice data.'

    def handle(self, *args, **options):
        # 1. Scrapy 프로젝트 설정 로드
        # settings를 사용하여 Scrapy의 설정(파이프라인, 지연 시간 등)을 적용합니다.
        try:
            # 이 함수는 scrapy.cfg 파일을 찾아 설정을 로드합니다.
            settings = get_project_settings()
        except KeyError:
            self.stdout.write(self.style.ERROR("Scrapy 프로젝트 설정을 로드할 수 없습니다. cbnu_crawler/settings.py 경로를 확인해주세요."))
            return

        # 2. CrawlerProcess 초기화
        process = CrawlerProcess(settings)

        # 3. 스파이더 실행
        self.stdout.write(self.style.NOTICE(">>> 충북대 공지사항 크롤링 시작... (Ctrl+C로 중단 가능)"))
        
        # CbnuNoticeSpider를 Process에 추가
        process.crawl(CbnuNoticeSpider)
        
        # 블록킹 모드로 크롤링 시작
        try:
            process.start()
            self.stdout.write(self.style.SUCCESS(">>> 크롤링 완료. 데이터베이스에 저장되었습니다."))
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\n>>> 크롤링이 사용자에 의해 중단되었습니다."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n>>> 크롤링 중 오류 발생: {e}"))