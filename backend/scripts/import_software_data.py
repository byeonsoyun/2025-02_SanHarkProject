#!/usr/bin/env python
"""소프트웨어학부 크롤링 데이터 DB 저장 및 임베딩"""

import os
import sys
import django
import json
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from chat.models import ChbNotice, NoticeRagIndex
from sentence_transformers import SentenceTransformer

print("🚀 소프트웨어학부 데이터 임포트 시작...")
print("="*60)

# 임베딩 모델 로드
print("📦 임베딩 모델 로딩...")
embedder = SentenceTransformer("jhgan/ko-sroberta-multitask")
print("✅ 모델 로드 완료")

# 크롤링 결과 로드
json_path = os.path.join(BASE_DIR, 'software_crawl_complete.json')
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"\n📊 데이터 로드:")
print(f"   - 공지사항: {len(data['notices'])}건")
print(f"   - 정적정보: {len(data['static_info'])}건")

# 공지사항 저장
print("\n" + "="*60)
print("💾 공지사항 저장 및 임베딩")
print("="*60)

notice_count = 0
for item in data['notices']:
    try:
        # notice_id 생성
        url_parts = item['url'].split('/')
        notice_id = f"sw_{url_parts[-1]}" if url_parts[-1].isdigit() else f"sw_{hash(item['url']) % 1000000}"
        
        # DB 저장
        notice, created = ChbNotice.objects.update_or_create(
            notice_id=notice_id,
            defaults={
                'board_type': item['board_type'],
                'title': item['title'],
                'content': item['content'],
                'source_url': item['url'],
                'post_date': datetime.strptime(item['post_date'], '%Y-%m-%d').date(),
                'is_active': True
            }
        )
        
        if created:
            # 임베딩 생성
            embedding = embedder.encode(item['content']).tolist()
            
            # RAG 인덱스 저장
            NoticeRagIndex.objects.update_or_create(
                notice=notice,
                chunk_index=0,
                defaults={
                    'text': item['content'],
                    'embedding': embedding
                }
            )
            
            notice_count += 1
            if notice_count % 10 == 0:
                print(f"   진행: {notice_count}건...")
    
    except Exception as e:
        print(f"   ❌ 오류 ({item['title'][:30]}...): {e}")
        continue

print(f"✅ 공지사항 {notice_count}건 저장 완료")

# 정적정보 저장
print("\n" + "="*60)
print("💾 정적정보 저장 및 임베딩")
print("="*60)

static_count = 0
for item in data['static_info']:
    try:
        # notice_id 생성
        title_key = item['title'].replace('-', '_').replace(' ', '_')
        notice_id = f"sw_static_{title_key}"
        
        # DB 저장
        notice, created = ChbNotice.objects.update_or_create(
            notice_id=notice_id,
            defaults={
                'board_type': item['board_type'],
                'title': item['title'],
                'content': item['content'],
                'source_url': item['url'],
                'post_date': datetime.now().date(),
                'is_active': True
            }
        )
        
        if created:
            # 임베딩 생성
            embedding = embedder.encode(item['content']).tolist()
            
            # RAG 인덱스 저장
            NoticeRagIndex.objects.update_or_create(
                notice=notice,
                chunk_index=0,
                defaults={
                    'text': item['content'],
                    'embedding': embedding
                }
            )
            
            static_count += 1
    
    except Exception as e:
        print(f"   ❌ 오류 ({item['title'][:30]}...): {e}")
        continue

print(f"✅ 정적정보 {static_count}건 저장 완료")

print("\n" + "="*60)
print("✅ 전체 임포트 완료!")
print("="*60)
print(f"📊 최종 결과:")
print(f"   - 공지사항: {notice_count}건")
print(f"   - 정적정보: {static_count}건")
print(f"   - 총합: {notice_count + static_count}건")
print("="*60)
