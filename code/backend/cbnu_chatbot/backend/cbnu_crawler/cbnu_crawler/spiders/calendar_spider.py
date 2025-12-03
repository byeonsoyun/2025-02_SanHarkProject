import scrapy
from datetime import datetime
import re

class CalendarSpider(scrapy.Spider):
    name = "calendar"
    start_urls = ['https://www.cbnu.ac.kr/www/selectWebSchdulList.do?key=455&schdulSeNo=1']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 1.5,
        'ROBOTSTXT_OBEY': False,
    }
    
    def parse(self, response):
        """학사일정 테이블 파싱"""
        from cbnu_crawler.spiders.cbnu_notice_spider import ChbNoticeItem
        
        rows = response.xpath('//table//tr[td]')
        
        for row in rows:
            cols = row.xpath('./td')
            if len(cols) < 2:
                continue
            
            col1_text = ''.join(cols[0].xpath('.//text()').getall()).strip()
            col2_text = ''.join(cols[1].xpath('.//text()').getall()).strip()
            
            if not col1_text or not col2_text:
                continue
            
            date_range = col1_text
            event = col2_text
            
            # 날짜에서 월 추출
            date_match = re.search(r'(\d{2})\.(\d{2})', date_range)
            if not date_match:
                continue
            
            month_num = date_match.group(1)
            day_num = date_match.group(2)
            
            notice_id = f"calendar_2025_{month_num}_{hash(date_range + event)}"
            title = f"[{month_num}월] {event}"
            content = f"일시: {date_range}\n내용: {event}"
            
            try:
                post_date = datetime(2025, int(month_num), int(day_num)).date()
            except:
                post_date = datetime.now().date()
            
            item = ChbNoticeItem()
            item['notice_id'] = notice_id
            item['title'] = title
            item['content'] = content
            item['url'] = response.url
            item['post_date'] = post_date
            item['board_type'] = '학사일정'
            
            yield item
