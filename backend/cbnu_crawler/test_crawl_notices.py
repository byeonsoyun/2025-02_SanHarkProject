#!/usr/bin/env python
"""학부공지사항 크롤링 - 고정 공지 예외 처리"""

import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
import time
import json

# 프로젝트 루트 경로
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

print("🚀 학부공지사항 크롤링 시작...")
print("="*60)

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

print("📦 ChromeDriver 준비 중...")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.implicitly_wait(10)
print("✅ ChromeDriver 준비 완료")

six_months_ago = datetime.now() - timedelta(days=180)
print(f"✅ 6개월 전 기준: {six_months_ago.strftime('%Y-%m-%d')}")
results = []

def parse_date(date_str):
    try:
        date_str = date_str.replace('.', '-').replace('/', '-').strip()
        return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        return None

try:
    url = 'https://software.cbnu.ac.kr/sub0401'
    print(f"\n📋 URL: {url}")
    
    driver.get(url)
    time.sleep(3)
    print("✅ 페이지 로드 완료")
    
    articles = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
    print(f"✅ 발견된 게시글: {len(articles)}개\n")
    
    article_data = []
    for article in articles:
        try:
            # 고정 공지 확인 (td.no에 "공지" 텍스트가 있는지)
            is_pinned = False
            try:
                no_elem = article.find_element(By.CSS_SELECTOR, 'td.no')
                if '공지' in no_elem.text:
                    is_pinned = True
            except:
                pass
            
            title_elem = article.find_element(By.CSS_SELECTOR, 'td.title a')
            title = title_elem.text.strip()
            link = title_elem.get_attribute('href')
            
            date_elem = article.find_element(By.CSS_SELECTOR, 'td.time')
            date_str = date_elem.text.strip()
            post_date = parse_date(date_str)
            
            if title and link and post_date:
                article_data.append({
                    'title': title,
                    'link': link,
                    'post_date': post_date,
                    'is_pinned': is_pinned
                })
        except:
            continue
    
    print(f"✅ 파싱된 게시글: {len(article_data)}개")
    pinned_count = sum(1 for a in article_data if a['is_pinned'])
    print(f"   - 고정 공지: {pinned_count}개")
    print(f"   - 일반 게시글: {len(article_data) - pinned_count}개\n")
    
    count = 0
    for idx, data in enumerate(article_data, 1):
        try:
            # 고정 공지는 날짜 무관하게 수집
            if data['is_pinned']:
                print(f"   📌 {count+1}. [고정] {data['title'][:50]}...")
                print(f"      날짜: {data['post_date'].strftime('%Y-%m-%d')}")
            else:
                # 일반 게시글은 6개월 필터 적용
                if data['post_date'] < six_months_ago:
                    print(f"   ⏭️  {idx}. 오래된 게시글: {data['title'][:40]}... ({data['post_date'].strftime('%Y-%m-%d')})")
                    continue
                
                print(f"   📄 {count+1}. {data['title'][:50]}...")
                print(f"      날짜: {data['post_date'].strftime('%Y-%m-%d')}")
            
            # 상세 페이지
            driver.get(data['link'])
            time.sleep(1)
            
            try:
                content_elem = driver.find_element(By.CSS_SELECTOR, 'div.board_view, div.xe_content, div.content')
                content = content_elem.text.strip()
                print(f"      내용: {len(content)}자")
            except:
                content = data['title']
                print(f"      ⚠️  내용 추출 실패")
            
            results.append({
                'board_type': '학부공지사항',
                'title': data['title'],
                'content': content,
                'url': data['link'],
                'post_date': data['post_date'].strftime('%Y-%m-%d'),
                'is_pinned': data['is_pinned']
            })
            
            count += 1
            
        except Exception as e:
            print(f"   ❌ {idx}. 오류: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"✅ 크롤링 완료: {count}건 수집")
    pinned_collected = sum(1 for r in results if r['is_pinned'])
    print(f"   - 고정 공지: {pinned_collected}건")
    print(f"   - 일반 게시글: {count - pinned_collected}건")
    
    output_file = os.path.join(BASE_DIR, 'test_crawl_result.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 결과 저장: {output_file}")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ 오류: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()
    print("\n✅ 브라우저 종료")
    print("\n🎉 테스트 완료!")
