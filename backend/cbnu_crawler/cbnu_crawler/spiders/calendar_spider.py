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
        current_year = datetime.now().year
        
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
            
            month_num = int(date_match.group(1))
            day_num = int(date_match.group(2))
            
            # 학년도 계산: 1~2월은 전년도 2학기, 3~8월은 1학기, 9~12월은 2학기
            if month_num in [1, 2]:
                # 1~2월은 전년도 2학기 (예: 2025년 1월 = 2024학년도 2학기)
                year = current_year
                academic_year = current_year - 1
            elif month_num >= 9:
                # 9~12월은 해당연도 2학기 (예: 2024년 12월 = 2024학년도 2학기)
                year = current_year - 1  # 작년 12월 데이터
                academic_year = current_year - 1
            else:
                # 3~8월은 해당연도 1학기
                year = current_year
                academic_year = current_year
            
            notice_id = f"calendar_{academic_year}_{month_num}_{hash(date_range + event)}"
            title = f"[{month_num}월] {event}"
            content = f"일시: {date_range}\n내용: {event}\n학년도: {academic_year}학년도"
            
            try:
                post_date = datetime(year, month_num, day_num).date()
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
