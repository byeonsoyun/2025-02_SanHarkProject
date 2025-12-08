from django.db import models
from pgvector.django import VectorField


class ChatMessage(models.Model):
    """채팅 메시지"""
    session_id = models.CharField(max_length=255, db_index=True, verbose_name='채팅 세션 ID')
    user_id = models.CharField(max_length=255, db_index=True, verbose_name='사용자 ID')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='시간')
    role = models.CharField(max_length=10, verbose_name='역할')  # user or assistant
    content = models.TextField(verbose_name='메시지 내용')

    class Meta:
        verbose_name = '채팅 메시지'
        verbose_name_plural = '채팅 메시지 목록'
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.role}] {self.content[:50]}"


class ChbNotice(models.Model):
    """충북대 공지사항"""
    notice_id = models.CharField(max_length=255, primary_key=True, unique=True, verbose_name='공지사항 고유 ID')
    board_type = models.CharField(max_length=100, db_index=True, verbose_name='게시판 종류')
    title = models.CharField(max_length=512, verbose_name='제목')
    content = models.TextField(verbose_name='본문 내용')
    source_url = models.URLField(max_length=512, verbose_name='원본 URL')
    post_date = models.DateField(verbose_name='게시일')
    added_date = models.DateTimeField(auto_now_add=True, verbose_name='DB 추가일')
    is_active = models.BooleanField(default=True, verbose_name='활성 상태')

    class Meta:
        verbose_name = '충북대 공지사항'
        verbose_name_plural = '충북대 공지사항 목록'
        ordering = ['-post_date']
        db_table = 'chat_chbnotice'

    def __str__(self):
        return f"[{self.board_type}] {self.title}"


class NoticeRagIndex(models.Model):
    """공지사항 RAG 벡터 인덱스"""
    notice = models.ForeignKey(ChbNotice, on_delete=models.CASCADE, related_name='rag_chunks', verbose_name='공지사항')
    chunk_index = models.IntegerField(verbose_name='청크 인덱스')
    text = models.TextField(verbose_name='청크 텍스트')
    embedding = VectorField(dimensions=768, verbose_name='벡터 임베딩')

    class Meta:
        verbose_name = '공지사항 RAG 인덱스'
        verbose_name_plural = '공지사항 RAG 인덱스 목록'
        db_table = 'notice_rag_index_table'
        unique_together = [['notice', 'chunk_index']]

    def __str__(self):
        return f"{self.notice.title} - Chunk {self.chunk_index}"


class UserEvent(models.Model):
    """사용자 일정"""
    user_id = models.CharField(max_length=255, db_index=True, verbose_name='사용자 ID')
    title = models.CharField(max_length=255, verbose_name='일정 제목')
    start_date = models.DateField(verbose_name='시작일')
    end_date = models.DateField(null=True, blank=True, verbose_name='종료일')
    description = models.TextField(blank=True, verbose_name='설명')
    google_event_id = models.CharField(max_length=255, null=True, blank=True, verbose_name='구글 캘린더 이벤트 ID')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')

    class Meta:
        verbose_name = '사용자 일정'
        verbose_name_plural = '사용자 일정 목록'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.user_id} - {self.title}"


class GoogleCalendarToken(models.Model):
    """구글 캘린더 토큰"""
    user_id = models.CharField(max_length=255, unique=True, verbose_name='사용자 ID')
    access_token = models.TextField(verbose_name='액세스 토큰')
    refresh_token = models.TextField(null=True, blank=True, verbose_name='리프레시 토큰')
    token_expiry = models.DateTimeField(verbose_name='토큰 만료일')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        verbose_name = '구글 캘린더 토큰'
        verbose_name_plural = '구글 캘린더 토큰 목록'

    def __str__(self):
        return f"Token for {self.user_id}"
