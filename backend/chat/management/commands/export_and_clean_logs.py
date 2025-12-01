import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from user_mgmt.models import ChatHistory # 사용자가 만든 모델 import

# 프로젝트 루트 경로 설정 (logs 폴더를 프로젝트 루트에 만들기 위함)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Command(BaseCommand):
    help = '대화 로그를 CSV로 백업하고 DB에서 모두 삭제합니다.'

    def handle(self, *args, **options):
        
        # 1. 백업 파일 경로 설정 및 logs 폴더 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = os.path.join(PROJECT_ROOT, 'logs') # 프로젝트 루트에 logs 폴더 지정
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_name = os.path.join(log_dir, f"chat_logs_{timestamp}.csv")
        
        # 2. 로그 데이터 가져오기
        logs = ChatHistory.objects.all().order_by('timestamp')
        log_count = logs.count()
        
        if log_count == 0:
            self.stdout.write(self.style.WARNING('DB에 저장된 대화 로그가 없습니다. 백업/삭제 건너뛰기.'))
            return

        # 3. CSV 파일로 데이터 쓰기 (백업 실행)
        with open(file_name, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Timestamp', 'Session_ID', 'Question', 'Answer'])
            for log in logs:
                writer.writerow([
                    log.id, 
                    log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    log.user_session_id, 
                    log.question, 
                    log.answer
                ])

        # 4. DB 내용 삭제 (테이블 초기화)
        logs.delete()
        
        self.stdout.write(self.style.SUCCESS(
            f'✅ 성공적으로 {log_count}개의 로그를 백업하고 DB에서 삭제했습니다.'
        ))
        self.stdout.write(self.style.SUCCESS(f'   백업 파일 경로: {file_name}'))