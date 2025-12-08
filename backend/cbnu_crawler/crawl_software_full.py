#!/usr/bin/env python
"""소프트웨어학부 전체 크롤링"""

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

print("🚀 소프트웨어학부 전체 크롤링 시작...")
print("="*60)

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.implicitly_wait(10)

six_months_ago = datetime.now() - timedelta(days=180)
year_2022 = datetime(2022, 1, 1)

results = {
    'notices': [],
    'static_info': []
}

def parse_date(date_str):
    try:
        date_str = date_str.replace('.', '-').replace('/', '-').strip()
        return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        return None

def crawl_notices(url, board_type, date_filter):
    """공지사항 크롤링"""
    print(f"\n{'='*60}")
    print(f"📋 [{board_type}] 크롤링 시작...")
    print(f"   URL: {url}")
    
    try:
        driver.get(url)
        time.sleep(3)
        
        articles = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
        print(f"   발견: {len(articles)}개")
        
        article_data = []
        for article in articles:
            try:
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
        
        count = 0
        for data in article_data:
            try:
                # 고정 공지는 날짜 무관
                if data['is_pinned']:
                    pass
                else:
                    # 날짜 필터 적용
                    if date_filter == 'six_months' and data['post_date'] < six_months_ago:
                        continue
                    elif date_filter == 'year_2022' and data['post_date'] < year_2022:
                        continue
                
                driver.get(data['link'])
                time.sleep(1)
                
                try:
                    content_elem = driver.find_element(By.CSS_SELECTOR, 'div.board_view, div.xe_content, div.content')
                    content = content_elem.text.strip()
                except:
                    content = data['title']
                
                results['notices'].append({
                    'board_type': board_type,
                    'title': data['title'],
                    'content': content,
                    'url': data['link'],
                    'post_date': data['post_date'].strftime('%Y-%m-%d'),
                    'is_pinned': data['is_pinned']
                })
                
                count += 1
                if count % 5 == 0:
                    print(f"   진행: {count}건...")
                
            except Exception as e:
                continue
        
        print(f"   ✅ 완료: {count}건 수집")
        
    except Exception as e:
        print(f"   ❌ 오류: {e}")

def crawl_static_page(url, page_type):
    """정적 페이지 크롤링"""
    print(f"\n📄 [{page_type}] 크롤링...")
    
    try:
        driver.get(url)
        time.sleep(2)
        
        try:
            content_elem = driver.find_element(By.CSS_SELECTOR, 'div.sub_content, div.content_area, div.content, div.xe_content')
            content = content_elem.text.strip()
        except:
            content = driver.find_element(By.TAG_NAME, 'body').text.strip()
        
        # 링크 정보 추출
        if '연구실' in page_type or '동아리' in page_type:
            try:
                links = driver.find_elements(By.CSS_SELECTOR, 'a[href]')
                link_info = []
                for link in links:
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    if href and text and len(text) > 2 and 'http' in href:
                        link_info.append(f"{text}: {href}")
                
                if link_info:
                    content += "\n\n[링크 정보]\n" + "\n".join(link_info[:20])
            except:
                pass
        
        results['static_info'].append({
            'page_type': page_type,
            'title': page_type,
            'content': content[:10000],
            'url': url
        })
        
        print(f"   ✅ 완료 ({len(content)}자)")
        
    except Exception as e:
        print(f"   ❌ 오류: {e}")

try:
    start_time = time.time()
    
    # 1. 공지사항 (최근 6개월)
    print("\n" + "="*60)
    print("📢 공지사항 크롤링 시작")
    print("="*60)
    
    crawl_notices('https://software.cbnu.ac.kr/sub0401', '학부공지사항', 'six_months')
    crawl_notices('https://software.cbnu.ac.kr/sub0305', '대학원공지사항', 'six_months')
    crawl_notices('https://software.cbnu.ac.kr/sub0402', '취업정보', 'six_months')
    crawl_notices('https://software.cbnu.ac.kr/sub0501', '휴학/상담/기타', 'year_2022')
    
    # 2. 정적 페이지
    print("\n" + "="*60)
    print("📚 정적 페이지 크롤링 시작")
    print("="*60)
    
    static_pages = [
        ('https://software.cbnu.ac.kr/sub0101', '학부소개-개요'),
        ('https://software.cbnu.ac.kr/sub0102', '학부소개-교육목표'),
        ('https://software.cbnu.ac.kr/sub0103', '학부소개-연혁'),
        ('https://software.cbnu.ac.kr/sub0104', '학부소개-발전전략'),
        ('https://software.cbnu.ac.kr/sub0105', '학부소개-구성원'),
        ('https://software.cbnu.ac.kr/sub0106', '학부소개-사무분장'),
        ('https://software.cbnu.ac.kr/sub0107', '학부소개-홍보자료'),
        ('https://software.cbnu.ac.kr/sub0108', '학부소개-찾아오시는길'),
        ('https://software.cbnu.ac.kr/sub0201', '학사정보-졸업요건'),
        ('https://software.cbnu.ac.kr/sub0202', '학사정보-전공교육과정'),
        ('https://software.cbnu.ac.kr/sub0203', '학사정보-교과목개요'),
        ('https://software.cbnu.ac.kr/sub0204', '학사정보-선수과목'),
        ('https://software.cbnu.ac.kr/sub0205', '학사정보-전공교육과정관계도'),
        ('https://software.cbnu.ac.kr/sub0302', '대학원-대학원교육과정'),
        ('https://software.cbnu.ac.kr/sub0303', '대학원-연구실소개'),
        ('https://software.cbnu.ac.kr/sub0403', '커뮤니티-동아리소개'),
    ]
    
    for url, page_type in static_pages:
        crawl_static_page(url, page_type)
    
    elapsed = time.time() - start_time
    
    print("\n" + "="*60)
    print("✅ 전체 크롤링 완료!")
    print("="*60)
    print(f"📊 수집 결과:")
    print(f"   - 공지사항: {len(results['notices'])}건")
    print(f"   - 정적정보: {len(results['static_info'])}건")
    print(f"   - 총합: {len(results['notices']) + len(results['static_info'])}건")
    print(f"⏱️  소요시간: {elapsed/60:.1f}분")
    
    output_file = os.path.join(BASE_DIR, 'software_crawl_result.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"💾 결과 저장: {output_file}")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ 오류: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()
    print("\n✅ 브라우저 종료")
