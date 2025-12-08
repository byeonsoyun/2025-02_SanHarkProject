from django.contrib import admin
from .models import ChatMessage, ChbNotice, NoticeRagIndex, UserEvent, GoogleCalendarToken

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'user_id', 'role', 'timestamp')
    list_filter = ('role', 'timestamp')
    search_fields = ('session_id', 'user_id', 'content')

@admin.register(ChbNotice)
class ChbNoticeAdmin(admin.ModelAdmin):
    list_display = ('notice_id', 'title', 'board_type', 'post_date', 'is_active')
    list_filter = ('board_type', 'is_active', 'post_date')
    search_fields = ('title', 'content', 'notice_id')

@admin.register(NoticeRagIndex)
class NoticeRagIndexAdmin(admin.ModelAdmin):
    list_display = ('notice', 'chunk_index')
    search_fields = ('text',)

@admin.register(UserEvent)
class UserEventAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'title', 'start_date', 'end_date')
    list_filter = ('start_date',)
    search_fields = ('title', 'user_id')

@admin.register(GoogleCalendarToken)
class GoogleCalendarTokenAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'created_at', 'updated_at')
    search_fields = ('user_id',)
