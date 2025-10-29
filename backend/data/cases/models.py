from django.db import models

# -----------------------
# 법령 (조문 단위)
# -----------------------
class LawArticle(models.Model):
    law_name = models.CharField(max_length=200)          # 법 이름 (예: 지방세기본법)
    article_num = models.CharField(max_length=50)        # 제1조, 제2조 등
    article_title = models.CharField(max_length=200, blank=True)  # 제목 (예: 목적)
    article_content = models.TextField()                 # 본문 내용
    hseq = models.CharField(max_length=10, null=True, blank=True)


    def __str__(self):
        return f"{self.law_name} - {self.article_num} {self.article_title}"


# -----------------------
# 판례 (사건 단위)
# -----------------------
class CaseLaw(models.Model):
    case_title = models.CharField(max_length=300)         # 사건 제목
    court_name = models.CharField(max_length=100)         # 예: 대법원
    judgment_date = models.CharField(max_length=50)       # 선고일자 (2025. 7. 24.)
    case_number = models.CharField(max_length=100)        # 사건번호 (예: 2023다240299)
    content_summary = models.TextField(blank=True)        # 판결요지 / 판시사항 요약
    full_text = models.TextField(blank=True)              # 전체 본문 (판결요지~이유까지)
    references = models.TextField(blank=True)             # 참조조문, 참조판례 등

    def __str__(self):
        return f"{self.case_title} ({self.case_number})"
