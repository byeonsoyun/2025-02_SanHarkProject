from django.urls import path
from .views import chat_message, upload_pdf, upload_json_csv

urlpatterns = [
    path('api/chat/', chat_message, name='chat_message'),   # chat/ → chat_message 뷰
    path('upload_pdf/', upload_pdf, name='upload_pdf'),     # PDF 업로드 엔드포인트
    path('upload_data/', upload_json_csv, name='upload_data'), # JSON/CSV 업로드 엔드포인트
]
