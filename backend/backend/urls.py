from django.contrib import admin
from django.urls import path, include
from api import views as api_views
from chat import views as chat_views

# media파일을 서비스하도록 연결
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', api_views.home, name='home'),
    path('chat/', include('chat.urls')),
    path('api/chat/', chat_views.chat_message, name='chat_api'),
]

# media부분
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
