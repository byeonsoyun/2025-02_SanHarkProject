#!/usr/bin/env python
"""크롤링 데이터를 DB에 저장"""

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

from chat.models import ChbNotice

print("📦 소프트웨어학부 데이터 DB 저장 시작...")
print("="*60)

# 크롤링 결과 로드
json_path = os.path.join(BASE_DIR, 'software_crawl_result.json')
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 1. 공지사항 저장
print(f"\n📢 공지사항 저장 중... ({len(data['notices'])}건)")

saved_count = 0
updated_count = 0
skipped_count = 0

for notice in data['notices']:
    try:
        # notice_id 생성 (URL 기반)
        notice_id = f"sw_{notice['url'].split('/')[-1]}"
        
        # board_type에 "소프트웨어학부-" 접두사 추가
        board_type = f"소프트웨어학부-{notice['board_type']}"
        
        # 날짜 변환
        post_date = datetime.strptime(notice['post_date'], '%Y-%m-%d').date()
        
        # 저장 또는 업데이트
        obj, created = ChbNotice.objects.update_or_create(
            notice_id=notice_id,
            defaults={
                'board_type': board_type,
                'title': notice['title'],
                'content': notice['content'],
                'source_url': notice['url'],
                'post_date': post_date,
                'is_active': True
            }
        )
        
        if created:
            saved_count += 1
            if saved_count % 10 == 0:
                print(f"   저장: {saved_count}건...")
        else:
            updated_count += 1
            
    except Exception as e:
        print(f"   ❌ 오류: {notice['title'][:30]}... - {e}")
        skipped_count += 1

print(f"\n✅ 공지사항 저장 완료:")
print(f"   - 신규 저장: {saved_count}건")
print(f"   - 업데이트: {updated_count}건")
print(f"   - 스킵: {skipped_count}건")

# 2. 정적 정보 저장 (공지사항 형태로)
print(f"\n📚 정적정보 저장 중... ({len(data['static_info'])}건)")

static_saved = 0
static_updated = 0

for info in data['static_info']:
    try:
        # notice_id 생성
        notice_id = f"sw_static_{info['page_type'].replace('-', '_')}"
        
        board_type = "소프트웨어학부-정적정보"
        
        obj, created = ChbNotice.objects.update_or_create(
            notice_id=notice_id,
            defaults={
                'board_type': board_type,
                'title': info['title'],
                'content': info['content'],
                'source_url': info['url'],
                'post_date': datetime.now().date(),
                'is_active': True
            }
        )
        
        if created:
            static_saved += 1
        else:
            static_updated += 1
            
    except Exception as e:
        print(f"   ❌ 오류: {info['title']} - {e}")

print(f"\n✅ 정적정보 저장 완료:")
print(f"   - 신규 저장: {static_saved}건")
print(f"   - 업데이트: {static_updated}건")

# 통계
total_sw = ChbNotice.objects.filter(board_type__startswith='소프트웨어학부').count()
print(f"\n📊 DB 통계:")
print(f"   - 소프트웨어학부 전체: {total_sw}건")

board_types = ChbNotice.objects.filter(board_type__startswith='소프트웨어학부').values_list('board_type', flat=True).distinct()
for bt in board_types:
    count = ChbNotice.objects.filter(board_type=bt).count()
    print(f"   - {bt}: {count}건")

print("\n" + "="*60)
print("✅ DB 저장 완료!")
