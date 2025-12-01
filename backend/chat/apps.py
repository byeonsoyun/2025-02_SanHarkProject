from django.apps import AppConfig
import os

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'

    def ready(self):
        """Initialize chat app - runs on server startup"""
        # Only run once during server startup
        if os.environ.get('RUN_MAIN', None) == 'true' or not os.environ.get('DJANGO_SETTINGS_MODULE'):
            try:
                from django.core.management import call_command
                
                print("=========================================================")
                print("🌟 [DB 초기화] 서버 재시작 감지: 로그 백업 및 삭제 명령 호출...")
                
                # Call the export and clean logs command
                call_command('export_and_clean_logs') 
                
                print("🌟 [DB 초기화] 백업/삭제 프로세스가 완료되었습니다.")
                print("=========================================================")
                
            except Exception as e:
                print(f"❌ [DB 초기화 오류] - 서버 구동은 계속됩니다: {e}")
