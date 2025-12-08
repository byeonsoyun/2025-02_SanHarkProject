#!/usr/bin/env python
"""소프트웨어학부 완전 크롤링 - SOFTWARE_PLAN.md 기준"""

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

print("🚀 소프트웨어학부 완전 크롤링 시작...")
print("="*60)

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

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
    print(f"\n📋 [{board_type}] 크롤링...")
    
    try:
        driver.get(url)
        time.sleep(3)
        
        articles = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
        
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
                if not data['is_pinned']:
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
                    'board_type': f'소프트웨어학부-{board_type}',
                    'title': data['title'],
                    'content': content,
                    'url': data['link'],
                    'post_date': data['post_date'].strftime('%Y-%m-%d')
                })
                
                count += 1
                
            except:
                continue
        
        print(f"   ✅ {count}건 수집")
        
    except Exception as e:
        print(f"   ❌ 오류: {e}")

def crawl_static_page(url, page_type):
    """정적 페이지 크롤링"""
    print(f"📄 [{page_type}] 크롤링...")
    
    try:
        driver.get(url)
        time.sleep(2)
        
        try:
            content_elem = driver.find_element(By.CSS_SELECTOR, 'div.sub_content, div.content_area, div.content, div.xe_content, body')
            content = content_elem.text.strip()
        except:
            content = driver.find_element(By.TAG_NAME, 'body').text.strip()
        
        # 404 체크
        if '404' in content or 'not found' in content.lower():
            print(f"   ⚠️  404 에러 - 페이지 없음")
            return
        
        # 링크 정보 추출 (연구실, 동아리)
        if '연구실' in page_type or '동아리' in page_type:
            try:
                links = driver.find_elements(By.CSS_SELECTOR, 'a[href]')
                link_info = []
                for link in links:
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    if href and text and len(text) > 2 and ('http' in href or 'software.cbnu.ac.kr' in href):
                        if text not in ['홈', '로그인', '회원가입', '검색']:
                            link_info.append(f"{text}: {href}")
                
                if link_info:
                    content += "\n\n[링크 정보]\n" + "\n".join(set(link_info[:30]))
            except:
                pass
        
        results['static_info'].append({
            'board_type': '소프트웨어학부-정적정보',
            'title': page_type,
            'content': content[:15000],
            'url': url
        })
        
        print(f"   ✅ 완료 ({len(content)}자)")
        
    except Exception as e:
        print(f"   ❌ 오류: {e}")

def crawl_graduation_requirements():
    """졸업요건 2021~2025학번 크롤링"""
    print(f"\n📋 졸업요건 (2021~2025학번) 크롤링...")
    
    base_url = 'https://software.cbnu.ac.kr/sub0501'
    
    # 졸업요건 페이지 접근
    try:
        driver.get(base_url)
        time.sleep(3)
        
        # 졸업요건 관련 게시글 찾기
        articles = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
        
        for article in articles:
            try:
                title_elem = article.find_element(By.CSS_SELECTOR, 'td.title a')
                title = title_elem.text.strip()
                link = title_elem.get_attribute('href')
                
                # 2021~2025학번 졸업요건만
                if '졸업요건' in title or '이수모형' in title:
                    for year in ['2021', '2022', '2023', '2024', '2025']:
                        if year in title:
                            driver.get(link)
                            time.sleep(1)
                            
                            try:
                                content_elem = driver.find_element(By.CSS_SELECTOR, 'div.board_view, div.xe_content, div.content')
                                content = content_elem.text.strip()
                            except:
                                content = title
                            
                            results['static_info'].append({
                                'board_type': '소프트웨어학부-정적정보',
                                'title': f'졸업요건-{year}학번',
                                'content': content,
                                'url': link
                            })
                            
                            print(f"   ✅ {year}학번 졸업요건 수집")
                            break
            except:
                continue
                
    except Exception as e:
        print(f"   ❌ 오류: {e}")

def crawl_graduation_project():
    """졸업작품 안내 크롤링"""
    print(f"\n📄 졸업작품 안내 크롤링...")
    
    url = 'https://software.cbnu.ac.kr/sub0501/7577'
    crawl_static_page(url, '학사정보-졸업작품안내')

try:
    start_time = time.time()
    
    # 1. 공지사항 (최근 6개월)
    print("\n" + "="*60)
    print("📢 공지사항 크롤링")
    print("="*60)
    
    crawl_notices('https://software.cbnu.ac.kr/sub0401', '학부공지사항', 'six_months')
    crawl_notices('https://software.cbnu.ac.kr/sub0305', '대학원공지사항', 'six_months')
    crawl_notices('https://software.cbnu.ac.kr/sub0402', '취업정보', 'six_months')
    crawl_notices('https://software.cbnu.ac.kr/sub0501', '휴학상담기타', 'year_2022')
    
    # 2. 학부소개
    print("\n" + "="*60)
    print("📚 학부소개")
    print("="*60)
    
    for i in range(1, 9):
        url = f'https://software.cbnu.ac.kr/sub010{i}'
        page_names = ['개요', '교육목표', '연혁', '발전전략', '구성원', '사무분장', '홍보자료', '찾아오시는길']
        crawl_static_page(url, f'학부소개-{page_names[i-1]}')
    
    # 3. 학사정보
    print("\n" + "="*60)
    print("📚 학사정보")
    print("="*60)
    
    crawl_graduation_requirements()  # 2021~2025학번 졸업요건
    crawl_graduation_project()  # 졸업작품 안내
    
    crawl_static_page('https://software.cbnu.ac.kr/sub0202', '학사정보-전공교육과정')
    crawl_static_page('https://software.cbnu.ac.kr/sub0203', '학사정보-교과목개요')
    crawl_static_page('https://software.cbnu.ac.kr/sub0204', '학사정보-선수과목')
    crawl_static_page('https://software.cbnu.ac.kr/sub0205', '학사정보-전공교육과정관계도')
    
    # 4. 대학원
    print("\n" + "="*60)
    print("📚 대학원")
    print("="*60)
    
    crawl_static_page('https://software.cbnu.ac.kr/sub0302', '대학원-대학원교육과정')
    crawl_static_page('https://software.cbnu.ac.kr/sub0303', '대학원-연구실소개')
    
    # 5. 커뮤니티
    print("\n" + "="*60)
    print("📚 커뮤니티")
    print("="*60)
    
    crawl_static_page('https://software.cbnu.ac.kr/sub0403', '커뮤니티-동아리소개')
    
    elapsed = time.time() - start_time
    
    print("\n" + "="*60)
    print("✅ 전체 크롤링 완료!")
    print("="*60)
    print(f"📊 수집 결과:")
    print(f"   - 공지사항: {len(results['notices'])}건")
    print(f"   - 정적정보: {len(results['static_info'])}건")
    print(f"   - 총합: {len(results['notices']) + len(results['static_info'])}건")
    print(f"⏱️  소요시간: {elapsed/60:.1f}분")
    
    output_file = os.path.join(BASE_DIR, 'software_crawl_complete.json')
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
