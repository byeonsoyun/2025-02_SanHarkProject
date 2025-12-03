#DB연동1차_apps.py파일 생성
'''현재는 apps.py 없이도 views.py와 RAG 로직이 정상적으로 로드되어 챗봇 기능 자체는 실행되고 있는 것입니다.

하지만 저희가 구현하려는 **"서버 시작 시 로그 자동 백업"**과 같은 자동 초기화 기능은 오직 apps.py의 ready() 함수를 통해서만 구현할 수 있기 때문에, 이 파일이 반드시 필요했던 것입니다.'''


# chat/apps.py 파일 내용

from django.apps import AppConfig
import os

class ChatConfig(AppConfig):
    # 기본 설정 유지
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'

    def ready(self):
        # 🌟 여기에 서버 시작 시 실행할 로직을 넣을 것입니다.
        # 기존 코드에서 복사해 온 ready() 로직을 여기에 넣습니다.
        if os.environ.get('RUN_MAIN', None) == 'true' or not os.environ.get('DJANGO_SETTINGS_MODULE'):
            try:
                from django.core.management import call_command
                
                print("=========================================================")
                print("🌟 [DB 초기화] 서버 재시작 감지: 로그 백업 및 삭제 명령 호출...")
                
                # Step 2에서 만든 명령어 이름 (export_and_clean_logs)을 호출
                call_command('export_and_clean_logs') 
                
                print("🌟 [DB 초기화] 백업/삭제 프로세스가 완료되었습니다.")
                print("=========================================================")
                
            except Exception as e:
                print(f"❌ [DB 초기화 오류] - 서버 구동은 계속됩니다: {e}")