import scrapy
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import re

class DormFinalSpider(scrapy.Spider):
    name = "dorm_final"
    
    custom_settings = {
        'DOWNLOAD_DELAY': 1.5,
        'ROBOTSTXT_OBEY': False,
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=chrome_options)
        self.one_year_ago = datetime.now() - timedelta(days=365)
    
    def closed(self, reason):
        self.driver.quit()
    
    def start_requests(self):
        # 1. 연락처
        yield scrapy.Request(url='https://dorm.chungbuk.ac.kr/home/sub.php?menukey=20016', callback=self.parse_contact)
        
        # 2. 위치안내
        locations = [
            ('본관', 'https://dorm.chungbuk.ac.kr/home/sub.php?menukey=20012'),
            ('양성재', 'https://dorm.chungbuk.ac.kr/home/sub.php?menukey=20013'),
            ('양진재', 'https://dorm.chungbuk.ac.kr/home/sub.php?menukey=20015'),
            ('양현재', 'https://dorm.chungbuk.ac.kr/home/sub.php?menukey=20014'),
        ]
        for name, url in locations:
            yield scrapy.Request(url=url, callback=self.parse_location, meta={'name': name})
        
        # 3. 공지사항
        yield scrapy.Request(url='https://dorm.chungbuk.ac.kr/home/sub.php?menukey=20039', callback=self.parse_notices)
        
        # 4. 식단
        today = datetime.now().strftime('%Y-%m-%d')
        menus = [
            ('본관', f'https://dorm.chungbuk.ac.kr/home/sub.php?menukey=20041&cur_day={today}&type=1'),
            ('양성재', f'https://dorm.chungbuk.ac.kr/home/sub.php?menukey=20041&type=2'),
            ('양진재', f'https://dorm.chungbuk.ac.kr/home/sub.php?menukey=20041&type=3'),
        ]
        for name, url in menus:
            yield scrapy.Request(url=url, callback=self.parse_menu, meta={'name': name})
    
    def parse_contact(self, response):
        self.driver.get(response.url)
        time.sleep(2)
        
        try:
            body = self.driver.find_element(By.TAG_NAME, 'body')
            text = body.text
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            content_lines = []
            
            for line in lines:
                if '연락처' in line or '043-' in line or '전화' in line or '팩스' in line:
                    content_lines.append(line)
                elif content_lines and len(content_lines) < 20:
                    if any(kw in line for kw in ['개성재', '계영원', '양성재', '양진재', '양현재', '행정실', '관리실']):
                        content_lines.append(line)
            
            content = '\n'.join(content_lines) if content_lines else text[:500]
            
            from cbnu_crawler.spiders.cbnu_notice_spider import ChbNoticeItem
            item = ChbNoticeItem()
            item['notice_id'] = 'dorm_contact'
            item['title'] = '기숙사 연락처 안내'
            item['content'] = content
            item['url'] = response.url
            item['post_date'] = datetime.now().date()
            item['board_type'] = '기숙사'
            yield item
        except Exception as e:
            self.logger.error(f"Error parsing contact: {e}")
    
    def parse_location(self, response):
        name = response.meta['name']
        self.driver.get(response.url)
        time.sleep(2)
        
        try:
            body = self.driver.find_element(By.TAG_NAME, 'body')
            text = body.text
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            content_lines = []
            
            for line in lines:
                if any(kw in line for kw in ['주소', '위치', '찾아오시는', '교통', '버스', '지도']):
                    content_lines.append(line)
                elif content_lines and len(content_lines) < 15:
                    if len(line) > 5 and not any(skip in line for skip in ['로그인', '검색', '메뉴']):
                        content_lines.append(line)
            
            content = '\n'.join(content_lines[:20]) if content_lines else text[:500]
            
            from cbnu_crawler.spiders.cbnu_notice_spider import ChbNoticeItem
            item = ChbNoticeItem()
            item['notice_id'] = f'dorm_location_{name}'
            item['title'] = f'기숙사 위치 안내 - {name}'
            item['content'] = content
            item['url'] = response.url
            item['post_date'] = datetime.now().date()
            item['board_type'] = '기숙사'
            yield item
        except Exception as e:
            self.logger.error(f"Error parsing location {name}: {e}")
    
    def parse_notices(self, response):
        notice_links = []
        
        # 1-6페이지 크롤링
        for page in range(1, 7):
            try:
                page_url = f'https://dorm.chungbuk.ac.kr/home/sub.php?menukey=20039&page={page}'
                self.driver.get(page_url)
                time.sleep(2)
                
                rows = self.driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
                
                for row in rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        if len(cells) < 3:
                            continue
                        
                        link_elem = row.find_element(By.TAG_NAME, 'a')
                        title = link_elem.text.strip().replace('[새글]', '').strip()
                        url = link_elem.get_attribute('href')
                        
                        post_date = None
                        for cell in cells:
                            date_text = cell.text.strip()
                            if re.match(r'\d{4}/\d{2}/\d{2}', date_text):
                                try:
                                    post_date = datetime.strptime(date_text, '%Y/%m/%d')
                                except:
                                    pass
                                break
                        
                        if post_date and post_date >= self.one_year_ago and title and url and 'mod=view' in url:
                            notice_links.append({'title': title, 'url': url, 'post_date': post_date.date()})
                    except:
                        continue
                
                self.logger.info(f"Page {page}: {len(notice_links)} notices collected so far")
            except Exception as e:
                self.logger.error(f"Error on page {page}: {e}")
        
        self.logger.info(f"Total {len(notice_links)} notices from 6 pages")
        
        # 상세 크롤링
        for idx, notice in enumerate(notice_links):
            try:
                self.driver.get(notice['url'])
                time.sleep(1.5)
                
                body_text = self.driver.find_element(By.TAG_NAME, 'body').text
                lines = body_text.split('\n')
                content_lines = []
                start_collecting = False
                
                for line in lines:
                    line = line.strip()
                    if '조회' in line or '등록일' in line:
                        start_collecting = True
                        continue
                    if start_collecting and ('다음글' in line or '이전글' in line or '목록' in line):
                        break
                    if start_collecting and line and len(line) > 2:
                        if not any(skip in line for skip in ['첨부파일', '다운로드', 'Kb)', 'Mb)']):
                            content_lines.append(line)
                
                content = '\n'.join(content_lines[:40]).strip()
                if len(content) < 50:
                    content = '\n'.join([l.strip() for l in lines if l.strip() and len(l.strip()) > 10])[:500]
                
                if content:
                    from cbnu_crawler.spiders.cbnu_notice_spider import ChbNoticeItem
                    no_match = re.search(r'no=(\d+)', notice['url'])
                    notice_id = f"dorm_{no_match.group(1)}" if no_match else f"dorm_{abs(hash(notice['url']))}"
                    
                    item = ChbNoticeItem()
                    item['notice_id'] = notice_id
                    item['title'] = notice['title']
                    item['content'] = content
                    item['url'] = notice['url']
                    item['post_date'] = notice['post_date']
                    item['board_type'] = '기숙사'
                    yield item
                    self.logger.info(f"Scraped {idx+1}/{len(notice_links)}: {notice['title'][:30]}")
            except Exception as e:
                self.logger.error(f"Error parsing notice: {e}")
    
    def parse_menu(self, response):
        name = response.meta['name']
        self.driver.get(response.url)
        time.sleep(3)
        
        try:
            # 테이블 형태로 식단 추출
            tables = self.driver.find_elements(By.TAG_NAME, 'table')
            menu_content = f"=== {name} 식단표 ===\n\n"
            
            for table in tables:
                try:
                    rows = table.find_elements(By.TAG_NAME, 'tr')
                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, 'td')
                        if not cells:
                            cells = row.find_elements(By.TAG_NAME, 'th')
                        
                        if cells:
                            row_text = ' | '.join([cell.text.strip() for cell in cells if cell.text.strip()])
                            if row_text and len(row_text) > 3:
                                menu_content += row_text + '\n'
                except:
                    continue
            
            # 테이블이 없으면 전체 텍스트에서 추출
            if len(menu_content) < 100:
                body = self.driver.find_element(By.TAG_NAME, 'body')
                text = body.text
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                menu_lines = [f"=== {name} 식단표 ===\n"]
                in_menu = False
                
                for line in lines:
                    if '요일' in line or '월' in line or '화' in line or '수' in line:
                        in_menu = True
                    if in_menu:
                        if '원산지' in line or '시간표' in line or '급식' in line:
                            break
                        if not any(skip in line for skip in ['로그인', '검색', '사이트맵', '알림마당', '메뉴열기']):
                            menu_lines.append(line)
                
                menu_content = '\n'.join(menu_lines[:100]) if len(menu_lines) > 1 else text[:1000]
            
            from cbnu_crawler.spiders.cbnu_notice_spider import ChbNoticeItem
            item = ChbNoticeItem()
            item['notice_id'] = f"dorm_menu_{name}_{datetime.now().strftime('%Y%m%d')}"
            item['title'] = f'기숙사 식단표 - {name}'
            item['content'] = menu_content
            item['url'] = response.url
            item['post_date'] = datetime.now().date()
            item['board_type'] = '기숙사'
            yield item
            self.logger.info(f"Scraped menu for {name}: {len(menu_content)} chars")
        except Exception as e:
            self.logger.error(f"Error parsing menu {name}: {e}")
