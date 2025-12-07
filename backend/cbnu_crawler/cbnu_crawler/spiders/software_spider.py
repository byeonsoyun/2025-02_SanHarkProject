import scrapy
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

class SoftwareSpider(scrapy.Spider):
    name = "software"
    start_urls = ['https://software.cbnu.ac.kr/sub0401']
    
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
        
        # 테이블에서 행 추출
        rows = self.driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
        
        for row in rows[:30]:
            try:
                # 제목 링크
                link_elem = row.find_element(By.CSS_SELECTOR, 'td a')
                title = link_elem.text.strip()
                url = link_elem.get_attribute('href')
                
                # 날짜
                try:
                    date_elem = row.find_element(By.CSS_SELECTOR, 'td:last-child')
                    date_text = date_elem.text.strip()
                except:
                    date_text = None
                
                if title and url and 'sub0401' in url:
                    # 상세 페이지 방문
                    self.driver.get(url)
                    time.sleep(1)
                    
                    try:
                        # 본문 내용 추출
                        content_elem = self.driver.find_element(By.CSS_SELECTOR, '.document_content, .xe_content, article')
                        content = content_elem.text.strip()
                        
                        if content:
                            from cbnu_crawler.spiders.cbnu_notice_spider import ChbNoticeItem
                            from urllib.parse import parse_qs, urlparse
                            
                            parsed = urlparse(url)
                            params = parse_qs(parsed.query)
                            doc_srl = params.get('document_srl', [''])[0]
                            notice_id = f"software_{doc_srl}" if doc_srl else f"software_{hash(url)}"
                            
                            try:
                                if date_text:
                                    for fmt in ['%Y.%m.%d', '%Y-%m-%d', '%Y. %m. %d']:
                                        try:
                                            post_date = datetime.strptime(date_text, fmt).date()
                                            break
                                        except:
                                            continue
                                    else:
                                        post_date = datetime.now().date()
                                else:
                                    post_date = datetime.now().date()
                            except:
                                post_date = datetime.now().date()
                            
                            item = ChbNoticeItem()
                            item['notice_id'] = notice_id
                            item['title'] = title
                            item['content'] = content
                            item['url'] = url
                            item['post_date'] = post_date
                            item['board_type'] = '소프트웨어학과'
                            
                            yield item
                            
                            # 목록으로 돌아가기
                            self.driver.back()
                            time.sleep(1)
                    except Exception as e:
                        self.logger.error(f"Error parsing detail {url}: {e}")
                        self.driver.back()
                        time.sleep(1)
            except Exception as e:
                self.logger.debug(f"Skipping row: {e}")
                continue
