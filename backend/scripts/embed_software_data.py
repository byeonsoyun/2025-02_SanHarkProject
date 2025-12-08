#!/usr/bin/env python
"""소프트웨어학부 데이터 임베딩 생성"""

import os
import sys
import django

# 프로젝트 루트를 Python 경로에 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from chat.models import ChbNotice
from chat.services import RAGService

print("🔮 소프트웨어학부 데이터 임베딩 생성 시작...")
print("="*60)

# RAG 서비스 초기화
rag_service = RAGService()

# 소프트웨어학부 데이터 가져오기
sw_notices = ChbNotice.objects.filter(board_type__startswith='소프트웨어학부', is_active=True)
print(f"\n📊 대상 데이터: {sw_notices.count()}건")

# 기존 인덱스에 추가 (별도 컬렉션 아님)
print(f"\n🔄 임베딩 생성 및 저장 중...")

success_count = 0
error_count = 0

for idx, notice in enumerate(sw_notices, 1):
    try:
        # 문서 준비
        doc_text = f"{notice.title}\n\n{notice.content}"
        
        metadata = {
            'notice_id': notice.notice_id,
            'board_type': notice.board_type,
            'title': notice.title,
            'url': notice.source_url,
            'post_date': notice.post_date.strftime('%Y-%m-%d'),
            'source': 'software'  # 소프트웨어학부 구분자
        }
        
        # 임베딩 생성 및 저장
        rag_service.add_document(doc_text, metadata)
        
        success_count += 1
        
        if idx % 10 == 0:
            print(f"   진행: {idx}/{sw_notices.count()}건...")
        
    except Exception as e:
        print(f"   ❌ 오류 [{notice.notice_id}]: {e}")
        error_count += 1

print(f"\n✅ 임베딩 생성 완료:")
print(f"   - 성공: {success_count}건")
print(f"   - 실패: {error_count}건")

# 전체 통계
total_vectors = rag_service.collection.count()
print(f"\n📊 벡터 DB 통계:")
print(f"   - 전체 벡터: {total_vectors}개")

print("\n" + "="*60)
print("✅ 임베딩 생성 완료!")
