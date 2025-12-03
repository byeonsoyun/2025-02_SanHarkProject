from django.contrib import admin
from django.urls import path, include
from api import views as api_views # 'api' 앱의 뷰를 사용하는 것으로 가정
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # 메인 페이지 뷰 (api 앱에 있는 것으로 가정)
    path('', api_views.home, name='home'), 
    
    # React 컴포넌트 경로의 접두사 '/chat/'에 맞춰 include 경로를 수정했습니다.
    # /chat/ 경로로 들어오는 모든 요청은 chat 앱의 urls.py로 전달됩니다.
    path('api/', include('chat.urls')), # '/chat/' 경로 제거
]

if settings.DEBUG:
    # 정적 파일 및 미디어 파일 설정 (개발 환경)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)