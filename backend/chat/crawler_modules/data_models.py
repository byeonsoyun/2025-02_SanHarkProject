# backend/chat/crawler_modules/data_models.py
# DB연동2차추가

from pydantic import BaseModel, Field
from typing import Optional

class LawData(BaseModel):
    """
    다양한 법률 데이터(판례, 법령 등)를 LawDocument 모델에 저장하기 위한 공통 스키마
    """
    document_id: str = Field(..., description="법령 또는 판례의 고유 식별자.")
    doc_type: str = Field(..., description="데이터 유형 (예: 판례, 법령, 행정규칙).")
    title: str = Field(..., description="법률 문서의 제목.")
    content: str = Field(..., description="법률 문서의 전체 내용 (RAG 학습 대상).")
    source_url: Optional[str] = Field(None, description="원본 데이터 조회 URL.")
    # 기타 필드는 필요에 따라 추가