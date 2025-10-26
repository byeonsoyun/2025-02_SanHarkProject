from django.urls import path
from .views import chat_message,  upload_pdf

urlpatterns = [
    path('api/chat/', chat_message, name='chat_message'),   # chat/ → chat_message 뷰
    path('upload_pdf/', upload_pdf),          # PDF 업로드 엔드포인트
]

