import scrapy
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import re

class DormSpider(scrapy.Spider):
    name = "dorm"
    start_urls = ['https://dorm.chungbuk.ac.kr/home/sub.php?menukey=20039']
    
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
    
    def closed(self, reason):
        self.driver.quit()
    
    def parse(self, response):
        self.driver.get(response.url)
        time.sleep(3)
        
        # 목록에서 URL과 제목 수집
        rows = self.driver.find_elements(By.CSS_SELECTOR, 'table tr')
        items = []
        
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td')
            if len(cells) >= 2:
                links = row.find_elements(By.TAG_NAME, 'a')
                if links:
                    title = links[0].text.strip()
                    url = links[0].get_attribute('href')
                    if title and url and 'mod=view' in url:
                        items.append({'title': title, 'url': url})
        
        # 각 URL 방문
        for item in items[:30]:
            self.driver.get(item['url'])
            time.sleep(1)
            
            try:
                # 본문 추출 - 전체 body에서 특정 패턴 찾기
                body = self.driver.find_element(By.TAG_NAME, 'body')
                full_text = body.text
                
                # "조회" 이후부터 "다음글" 전까지를 본문으로
                lines = full_text.split('\n')
                content_lines = []
                in_content = False
                
                for line in lines:
                    line = line.strip()
                    if '조회' in line and ('등록일' in line or '작성자' in line):
                        in_content = True
                        continue
                    if in_content:
                        if '다음글' in line or '이전글' in line:
                            break
                        if line and len(line) > 3 and '첨부' not in line and '다운로드' not in line:
                            content_lines.append(line)
                
                content = '\n'.join(content_lines).strip()
                
                if content:
                    from cbnu_crawler.spiders.cbnu_notice_spider import ChbNoticeItem
                    
                    no_match = re.search(r'no=(\d+)', item['url'])
                    notice_id = f"dorm_{no_match.group(1)}" if no_match else f"dorm_{hash(item['url'])}"
                    
                    # 날짜는 현재 날짜 사용 (목록에서 추출 어려움)
                    post_date = datetime.now().date()
                    
                    notice_item = ChbNoticeItem()
                    notice_item['notice_id'] = notice_id
                    notice_item['title'] = item['title']
                    notice_item['content'] = content
                    notice_item['url'] = item['url']
                    notice_item['post_date'] = post_date
                    notice_item['board_type'] = '기숙사'
                    
                    yield notice_item
            except Exception as e:
                self.logger.error(f"Error parsing {item['url']}: {e}")
