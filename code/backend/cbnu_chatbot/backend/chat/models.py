from django.db import models
from pgvector.django import VectorField

# 1. 채팅 기록 모델 (기존 재활용)
class ChatMessage(models.Model):
    """
    사용자와 챗봇의 대화 기록을 저장하는 모델.
    사용자 데이터는 user_mgmt 앱에서 관리되므로 여기서는 세션/사용자 ID만 참조합니다.
    """
    session_id = models.CharField(max_length=255, db_index=True, verbose_name="채팅 세션 ID")
    user_id = models.CharField(max_length=255, db_index=True, verbose_name="사용자 ID")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="시간")
    
    # role: 'user' 또는 'assistant'
    role = models.CharField(max_length=10, verbose_name="역할")
    
    # content: 대화 내용
    content = models.TextField(verbose_name="메시지 내용")

    class Meta:
        verbose_name = "채팅 메시지"
        verbose_name_plural = "채팅 메시지 목록"
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.session_id}] {self.role}: {self.content[:30]}..."


# 2. 공지사항 원본 데이터 저장 (RAG 시스템의 지식 원천)
class ChbNotice(models.Model):
    """
    충북대학교 공지사항 웹사이트에서 크롤링된 원본 데이터를 저장하는 모델.
    RAG 시스템의 지식 원천(Source)이 됩니다.
    """
    # 크롤링 시 생성되는 공지사항의 고유 번호 (주로 게시판 ID + 글 번호)
    notice_id = models.CharField(
        max_length=255, 
        unique=True, 
        primary_key=True,
        verbose_name="공지사항 고유 ID"
    ) 
    
    # 공지사항의 게시판 종류 (예: '일반공지', '학사공지', '장학공지')
    board_type = models.CharField(
        max_length=100, 
        db_index=True, 
        verbose_name="게시판 종류"
    )
    
    title = models.CharField(max_length=512, verbose_name="제목")
    content = models.TextField(verbose_name="본문 내용 (청크 분할 대상)")
    source_url = models.URLField(max_length=512, verbose_name="원본 URL")
    
    # 게시일자 (검색 시 최신 정보를 우선하기 위해 중요)
    post_date = models.DateField(verbose_name="게시일")
    
    # 데이터베이스에 추가된 시점
    added_date = models.DateTimeField(auto_now_add=True, verbose_name="DB 추가일")
    
    # 🌟 추가된 필드: 현재 크롤링에서 발견되었는지 여부
    is_active = models.BooleanField(default=True, verbose_name="현재 활성 상태")
    
    class Meta:
        verbose_name = "충북대 공지사항"
        verbose_name_plural = "충북대 공지사항 목록"
        ordering = ['-post_date']

    def __str__(self):
        return f"[{self.board_type}] {self.title}"


# 3. RAG 인덱스 저장소: 공지사항 청크와 벡터를 저장
class NoticeRagIndex(models.Model):
    """
    ChbNotice에서 분할된 텍스트 청크와 그 임베딩 벡터를 저장하는 모델.
    실제 RAG 검색(Retrieval)에 사용되며, pgvector 확장과 연동됩니다.
    """
    # 텍스트 청크 (실제 LLM에게 전달되는 문맥)
    text_chunk = models.TextField(verbose_name="텍스트 청크") 
    
    # 원본 공지사항 문서의 메타데이터 (notice_id, title, source_url, post_date 등)를 JSON 형태로 저장
    metadata = models.JSONField(blank=True, null=True, verbose_name="청크 메타데이터")
    
    # 임베딩 벡터 (기존과 동일하게 768차원 유지)
    embedding = VectorField(dimensions=768, verbose_name="청크 벡터 임베딩")
    
    # 원본 문서(ChbNotice)와의 관계 (선택적)
    # notice = models.ForeignKey(ChbNotice, on_delete=models.CASCADE, related_name='chunks', null=True)

    class Meta:
        # 이 모델이 'notice_rag_index_table'과 매핑되도록 설정
        db_table = 'notice_rag_index_table' 
        verbose_name = "공지사항 RAG 인덱스"
        verbose_name_plural = "공지사항 RAG 인덱스 목록"

    def __str__(self):
        pk = self.metadata.get('notice_id', 'Unknown')
        title = self.metadata.get('title', 'No Title')
        return f"Chunk #{self.pk} from {title} (ID: {pk})"