from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from django.conf import settings
from .models import GoogleCalendarToken
from datetime import datetime, timezone

class GoogleCalendarService:
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    @staticmethod
    def get_auth_url(user_id):
        """OAuth 인증 URL 생성"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
                }
            },
            scopes=GoogleCalendarService.SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',  # 항상 동의 화면 표시하여 refresh_token 받기
            state=user_id
        )
        return auth_url
    
    @staticmethod
    def handle_callback(code, user_id):
        """OAuth 콜백 처리 및 토큰 저장"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
                }
            },
            scopes=GoogleCalendarService.SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # 토큰 저장
        GoogleCalendarToken.objects.update_or_create(
            user_id=user_id,
            defaults={
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_expiry': credentials.expiry
            }
        )
        
        return True
    
    @staticmethod
    def get_credentials(user_id):
        """저장된 토큰으로 Credentials 객체 생성"""
        try:
            token = GoogleCalendarToken.objects.get(user_id=user_id)
            credentials = Credentials(
                token=token.access_token,
                refresh_token=token.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                scopes=GoogleCalendarService.SCOPES
            )
            return credentials
        except GoogleCalendarToken.DoesNotExist:
            return None
    
    @staticmethod
    def create_event(user_id, title, start_date, end_date=None, description=''):
        """구글 캘린더에 이벤트 생성"""
        credentials = GoogleCalendarService.get_credentials(user_id)
        if not credentials:
            return None
        
        service = build('calendar', 'v3', credentials=credentials)
        
        event = {
            'summary': title,
            'description': description,
            'start': {
                'date': start_date.isoformat(),
                'timeZone': 'Asia/Seoul',
            },
            'end': {
                'date': (end_date or start_date).isoformat(),
                'timeZone': 'Asia/Seoul',
            },
        }
        
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return created_event['id']
    
    @staticmethod
    def delete_event(user_id, google_event_id):
        """구글 캘린더에서 이벤트 삭제"""
        credentials = GoogleCalendarService.get_credentials(user_id)
        if not credentials:
            return False
        
        service = build('calendar', 'v3', credentials=credentials)
        
        try:
            service.events().delete(calendarId='primary', eventId=google_event_id).execute()
            return True
        except Exception as e:
            print(f"Google Calendar 삭제 실패: {e}")
            return False
