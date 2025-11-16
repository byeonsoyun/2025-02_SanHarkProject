#DB연동1차_사용자데이터저장모델
from django.db import models

# 1. 운영 데이터: 사용자 대화 기록 저장 (UserLog)
class ChatHistory(models.Model):
    user_session_id = models.CharField(max_length=255, verbose_name="사용자 세션 ID")
    question = models.TextField(verbose_name="사용자 질문")
    answer = models.TextField(verbose_name="챗봇 답변")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="기록 시각")
    
    class Meta:
        verbose_name = "대화 기록"
        verbose_name_plural = "대화 기록 목록"

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.user_session_id}: {self.question[:30]}..."


# 3. 사용자 업로드 문서 모델 (PDF, Docx 등)
class UploadedDocument(models.Model):
    """
    사용자가 업로드한 파일을 저장하고, 텍스트 추출 및 RAG 처리를 위한 메타데이터를 관리합니다.
    이 데이터는 공식 법률 문서(LawDocument)와 분리되어 사용자별 컨텍스트로 사용됩니다.
    """
    user_session_id = models.CharField(max_length=255, verbose_name="사용자 세션 ID")
    
    # 실제 파일은 settings.MEDIA_ROOT (현재 media 디렉토리)에 저장됩니다.
    file = models.FileField(upload_to='user_uploads/', verbose_name="업로드 파일")
    
    filename = models.CharField(max_length=255, verbose_name="파일명")
    
    # PDF에서 추출한 텍스트를 저장합니다. 이것이 RAG의 임시 지식 기반이 됩니다.
    extracted_text = models.TextField(blank=True, null=True, verbose_name="추출된 텍스트")
    
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="업로드 시각")
    
    # RAG 시스템의 벡터 DB에 임베딩 처리가 완료되었는지 확인하는 플래그
    is_rag_ready = models.BooleanField(default=False, verbose_name="RAG 처리 완료 여부")

    class Meta:
        verbose_name = "사용자 업로드 문서"
        verbose_name_plural = "사용자 업로드 문서 목록"

    def __str__(self):
        return f"[{self.user_session_id}] {self.filename}"


# 4. ChatHistory 모델 업데이트 (선택 사항: 파일과 대화 기록 연결)
# 만약 어떤 파일에 대해 질문했는지 정확히 추적하고 싶다면, ChatHistory 모델에 Foreign Key를 추가합니다.
# class ChatHistory(models.Model):
#     ...
#     uploaded_document = models.ForeignKey(
#         UploadedDocument, 
#         on_delete=models.SET_NULL, 
#         null=True, 
#         blank=True, 
#         verbose_name="참조 업로드 문서"
#     )
#     ...