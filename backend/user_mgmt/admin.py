from django.contrib import admin
from .models import ChatHistory, UploadedDocument

@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ['user_session_id', 'question', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['user_session_id', 'question']

@admin.register(UploadedDocument)
class UploadedDocumentAdmin(admin.ModelAdmin):
    list_display = ['user_session_id', 'filename', 'uploaded_at', 'is_rag_ready']
    list_filter = ['uploaded_at', 'is_rag_ready']
    search_fields = ['user_session_id', 'filename']
