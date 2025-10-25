from django.contrib import admin
from django.urls import path, include
from api import views  # home view 임포트

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/ping/', include('api.urls')),  # 기존
    path('', views.home, name='home'),       # 홈 페이지 추가
    path('cases/', include('data.cases.urls')),  # 앱 URL 연결
    path('chat/', include('chat.urls')),         # WebSocket
]
