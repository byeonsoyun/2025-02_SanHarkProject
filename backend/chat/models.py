#DB연동1차_chat/models.py 파일 추가
# chat/models.py 파일 내용

from django.db import models


# 2. 학습/검색 데이터: 확장형 법률 문서 통합 저장 (RAG 시스템의 지식 원천)
class LawDocument(models.Model):
    """
    판례, 법령, 조례 등 모든 법률 문서를 통합하여 관리하는 모델.
    RAG 시스템의 데이터 소스로 사용됩니다.
    """
    # ------------------ 확장성 핵심 필드 ------------------
    # 문서의 유형을 구분: PRECEDENT(판례), LAW(법령), ORDINANCE(조례)
    doc_type = models.CharField(
        max_length=20, 
        db_index=True, 
        verbose_name="문서 유형"
    )
    # API에서 제공하는 각 문서의 고유 ID를 저장 (판례일련번호, 법령ID 등)
    document_id = models.CharField(
        max_length=50, 
        unique=True, 
        primary_key=True,
        verbose_name="문서 고유 ID"
    ) 
    # -----------------------------------------------------
    
    title = models.CharField(max_length=512, verbose_name="문서 제목")
    content = models.TextField(verbose_name="문서 본문 (청킹 및 임베딩 대상)")
    
    source_url = models.URLField(max_length=512, blank=True, null=True, verbose_name="출처 URL")
    enforcement_date = models.CharField(max_length=8, verbose_name="시행/선고일자 (YYYYMMDD)")
    added_date = models.DateTimeField(auto_now_add=True, verbose_name="추가일")

    # 특화 필드 (유형별로 값이 비어있을 수 있음 - null=True, blank=True)
    case_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="사건번호")
    court_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="법원명")
    law_article_no = models.CharField(max_length=50, blank=True, null=True, verbose_name="조항 번호")

    class Meta:
        verbose_name = "통합 법률 문서"
        verbose_name_plural = "통합 법률 문서 목록"

    def __str__(self):
        return f"[{self.doc_type}] {self.title}"
    

