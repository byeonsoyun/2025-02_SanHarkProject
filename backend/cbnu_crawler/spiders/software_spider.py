import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import time
import re

class SoftwareSpider(scrapy.Spider):
    name = "software"
    allowed_domains = ["software.cbnu.ac.kr"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Selenium 설정
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        
        # 6개월 전 날짜
        self.six_months_ago = datetime.now() - timedelta(days=180)
        # 2022년 1월 1일
        self.year_2022 = datetime(2022, 1, 1)
        
        self.results = {
            'notices': [],  # 공지사항 타입
            'static_info': []  # 정적 정보 타입
        }
    
    def start_requests(self):
        # 공지사항 크롤링 (최근 6개월)
        yield scrapy.Request('https://software.cbnu.ac.kr/sub0401', 
                           callback=self.parse_notices,
                           meta={'board_type': '학부공지사항', 'date_filter': 'six_months'})
        
        yield scrapy.Request('https://software.cbnu.ac.kr/sub0305', 
                           callback=self.parse_notices,
                           meta={'board_type': '대학원공지사항', 'date_filter': 'six_months'})
        
        yield scrapy.Request('https://software.cbnu.ac.kr/sub0402', 
                           callback=self.parse_notices,
                           meta={'board_type': '취업정보', 'date_filter': 'six_months'})
        
        # 자료실 (2022년 이후)
        yield scrapy.Request('https://software.cbnu.ac.kr/sub0501', 
                           callback=self.parse_notices,
                           meta={'board_type': '휴학/상담/기타', 'date_filter': 'year_2022'})
        
        # 정적 페이지들
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
            yield scrapy.Request(url, 
                               callback=self.parse_static_page,
                               meta={'page_type': page_type})
    
    def parse_notices(self, response):
        """공지사항 게시판 크롤링"""
        board_type = response.meta['board_type']
        date_filter = response.meta['date_filter']
        
        self.driver.get(response.url)
        time.sleep(2)
        
        try:
            # 게시글 목록 찾기
            articles = self.driver.find_elements(By.CSS_SELECTOR, 'table.board_list tbody tr')
            
            for article in articles:
                try:
                    # 제목과 링크
                    title_elem = article.find_element(By.CSS_SELECTOR, 'td.title a')
                    title = title_elem.text.strip()
                    link = title_elem.get_attribute('href')
                    
                    # 날짜
                    date_elem = article.find_element(By.CSS_SELECTOR, 'td.date')
                    date_str = date_elem.text.strip()
                    
                    # 날짜 파싱
                    post_date = self.parse_date(date_str)
                    
                    if not post_date:
                        continue
                    
                    # 날짜 필터링
                    if date_filter == 'six_months' and post_date < self.six_months_ago:
                        continue
                    elif date_filter == 'year_2022' and post_date < self.year_2022:
                        continue
                    
                    # 상세 페이지 크롤링
                    self.driver.get(link)
                    time.sleep(1)
                    
                    content_elem = self.driver.find_element(By.CSS_SELECTOR, 'div.board_view_content')
                    content = content_elem.text.strip()
                    
                    self.results['notices'].append({
                        'board_type': board_type,
                        'title': title,
                        'content': content,
                        'url': link,
                        'post_date': post_date.strftime('%Y-%m-%d')
                    })
                    
                    self.logger.info(f"✅ [{board_type}] {title}")
                    
                    # 뒤로가기
                    self.driver.back()
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"게시글 파싱 실패: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"게시판 파싱 실패 [{board_type}]: {e}")
    
    def parse_static_page(self, response):
        """정적 페이지 크롤링"""
        page_type = response.meta['page_type']
        
        self.driver.get(response.url)
        time.sleep(2)
        
        try:
            # 페이지 전체 텍스트 추출
            content_elem = self.driver.find_element(By.CSS_SELECTOR, 'div.sub_content, div.content_area')
            content = content_elem.text.strip()
            
            # 특수 처리: 연구실 소개, 동아리 소개
            if '연구실소개' in page_type or '동아리소개' in page_type:
                # 각 항목별 링크 추출
                links = content_elem.find_elements(By.CSS_SELECTOR, 'a[href]')
                link_info = []
                for link in links:
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    if href and text:
                        link_info.append(f"{text}: {href}")
                
                if link_info:
                    content += "\n\n[링크 정보]\n" + "\n".join(link_info)
            
            self.results['static_info'].append({
                'page_type': page_type,
                'title': page_type,
                'content': content,
                'url': response.url
            })
            
            self.logger.info(f"✅ [정적페이지] {page_type}")
            
        except Exception as e:
            self.logger.error(f"정적 페이지 파싱 실패 [{page_type}]: {e}")
    
    def parse_date(self, date_str):
        """날짜 문자열을 datetime 객체로 변환"""
        try:
            # 2025-12-08, 2025.12.08, 2025/12/08 형식
            date_str = date_str.replace('.', '-').replace('/', '-')
            return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            try:
                # 12-08 형식 (올해)
                current_year = datetime.now().year
                return datetime.strptime(f"{current_year}-{date_str}", '%Y-%m-%d')
            except:
                return None
    
    def closed(self, reason):
        """크롤링 종료 시 처리"""
        self.driver.quit()
        
        # 결과 저장
        import json
        output_file = '/Users/sang/SanHark_CBNU/backend/software_crawl_result.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"✅ 크롤링 완료!")
        self.logger.info(f"   - 공지사항: {len(self.results['notices'])}건")
        self.logger.info(f"   - 정적정보: {len(self.results['static_info'])}건")
        self.logger.info(f"   - 결과 저장: {output_file}")
