#!/usr/bin/env python
"""
소프트웨어학부 크롤링 스크립트
백그라운드 실행: nohup python crawl_software.py > /tmp/software_crawl.log 2>&1 &
"""

import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
import time
import json

# 프로젝트 루트 경로
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class SoftwareCrawler:
    def __init__(self):
        print("🚀 소프트웨어학부 크롤러 시작...")
        
        # Selenium 설정
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        
        # 날짜 필터
        self.six_months_ago = datetime.now() - timedelta(days=180)
        self.year_2022 = datetime(2022, 1, 1)
        
        self.results = {
            'notices': [],
            'static_info': []
        }
    
    def parse_date(self, date_str):
        """날짜 파싱"""
        try:
            date_str = date_str.replace('.', '-').replace('/', '-').strip()
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            try:
                current_year = datetime.now().year
                return datetime.strptime(f"{current_year}-{date_str}", '%Y-%m-%d')
            except:
                return None
    
    def crawl_notices(self, url, board_type, date_filter):
        """공지사항 크롤링"""
        print(f"\n📋 [{board_type}] 크롤링 시작...")
        
        try:
            self.driver.get(url)
            time.sleep(3)
            
            # 게시글 목록
            articles = self.driver.find_elements(By.CSS_SELECTOR, 'table tbody tr, div.board_list li')
            print(f"   발견된 게시글: {len(articles)}개")
            
            count = 0
            for article in articles[:50]:  # 최대 50개
                try:
                    # 제목과 링크
                    title_elem = article.find_element(By.CSS_SELECTOR, 'a')
                    title = title_elem.text.strip()
                    link = title_elem.get_attribute('href')
                    
                    if not title or not link:
                        continue
                    
                    # 날짜
                    try:
                        date_elem = article.find_element(By.CSS_SELECTOR, 'td.date, span.date, div.date')
                        date_str = date_elem.text.strip()
                        post_date = self.parse_date(date_str)
                    except:
                        post_date = datetime.now()
                    
                    if not post_date:
                        continue
                    
                    # 날짜 필터링
                    if date_filter == 'six_months' and post_date < self.six_months_ago:
                        continue
                    elif date_filter == 'year_2022' and post_date < self.year_2022:
                        continue
                    
                    # 상세 페이지
                    self.driver.get(link)
                    time.sleep(1)
                    
                    try:
                        content_elem = self.driver.find_element(By.CSS_SELECTOR, 'div.board_view, div.content, div.view_content')
                        content = content_elem.text.strip()
                    except:
                        content = title
                    
                    self.results['notices'].append({
                        'board_type': board_type,
                        'title': title,
                        'content': content,
                        'url': link,
                        'post_date': post_date.strftime('%Y-%m-%d')
                    })
                    
                    count += 1
                    print(f"   ✅ {count}. {title[:50]}...")
                    
                    self.driver.back()
                    time.sleep(1)
                    
                except Exception as e:
                    continue
            
            print(f"   완료: {count}건 수집")
            
        except Exception as e:
            print(f"   ❌ 오류: {e}")
    
    def crawl_static_page(self, url, page_type):
        """정적 페이지 크롤링"""
        print(f"\n📄 [{page_type}] 크롤링 시작...")
        
        try:
            self.driver.get(url)
            time.sleep(2)
            
            # 페이지 내용
            try:
                content_elem = self.driver.find_element(By.CSS_SELECTOR, 'div.sub_content, div.content_area, div.content')
                content = content_elem.text.strip()
            except:
                content = self.driver.find_element(By.TAG_NAME, 'body').text.strip()
            
            # 링크 정보 추출 (연구실, 동아리)
            if '연구실' in page_type or '동아리' in page_type:
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href]')
                    link_info = []
                    for link in links:
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        if href and text and len(text) > 2:
                            link_info.append(f"{text}: {href}")
                    
                    if link_info:
                        content += "\n\n[링크 정보]\n" + "\n".join(link_info[:20])
                except:
                    pass
            
            self.results['static_info'].append({
                'page_type': page_type,
                'title': page_type,
                'content': content[:5000],  # 최대 5000자
                'url': url
            })
            
            print(f"   ✅ 완료 ({len(content)}자)")
            
        except Exception as e:
            print(f"   ❌ 오류: {e}")
    
    def run(self):
        """전체 크롤링 실행"""
        start_time = time.time()
        
        # 1. 공지사항 (최근 6개월)
        self.crawl_notices('https://software.cbnu.ac.kr/sub0401', '학부공지사항', 'six_months')
        self.crawl_notices('https://software.cbnu.ac.kr/sub0305', '대학원공지사항', 'six_months')
        self.crawl_notices('https://software.cbnu.ac.kr/sub0402', '취업정보', 'six_months')
        
        # 2. 자료실 (2022년 이후)
        self.crawl_notices('https://software.cbnu.ac.kr/sub0501', '휴학/상담/기타', 'year_2022')
        
        # 3. 정적 페이지
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
            self.crawl_static_page(url, page_type)
        
        # 종료
        self.driver.quit()
        
        # 결과 저장
        output_file = os.path.join(BASE_DIR, 'software_crawl_result.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        elapsed = time.time() - start_time
        
        print("\n" + "="*60)
        print("✅ 크롤링 완료!")
        print(f"   - 공지사항: {len(self.results['notices'])}건")
        print(f"   - 정적정보: {len(self.results['static_info'])}건")
        print(f"   - 소요시간: {elapsed/60:.1f}분")
        print(f"   - 결과파일: {output_file}")
        print("="*60)

if __name__ == '__main__':
    crawler = SoftwareCrawler()
    crawler.run()
