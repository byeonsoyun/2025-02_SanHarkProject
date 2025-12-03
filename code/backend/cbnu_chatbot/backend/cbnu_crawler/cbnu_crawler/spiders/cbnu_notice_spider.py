import scrapy
from urllib.parse import urlparse, parse_qs, urlunparse
from datetime import datetime, date
import re 
from urllib.parse import urljoin 

class ChbNoticeItem(scrapy.Item):
    """
    크롤링한 공지사항 데이터를 담는 Item
    *** 파이프라인과의 연동을 위해 필드 이름을 'source_url'에서 'url'로 변경합니다. ***
    """
    notice_id = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    url = scrapy.Field() # <-- 필드 이름 변경 (source_url -> url)
    post_date = scrapy.Field()
    board_type = scrapy.Field()


class CbnuNoticeSpider(scrapy.Spider):
    name = "cbnu_notice"
    # 시작 URL은 목록 페이지로 직접 리다이렉션되는 URL을 사용합니다.
    start_urls = ['https://www.cbnu.ac.kr/www/selectBbsNttList.do?bbsNo=8&key=813&pageIndex=1']

    # --- 💡 날짜 중단 조건 설정: 2024년 11월 1일 이전 공지는 크롤링하지 않습니다. ---
    STOP_DATE = date(2024, 11, 1)

    # 이미 요청을 보낸 게시물 번호(nttNo)를 저장하여 이중 등록(고정/일반) 중복을 방지합니다.
    crawled_ntt_nos = set()

    # Scrapy Settings
    custom_settings = {
        'DOWNLOAD_DELAY': 1.5,
        'ROBOTSTXT_OBEY': False,
        'LOG_LEVEL': 'DEBUG', # 추출된 문자열을 확인하기 위해 DEBUG 레벨 유지
        # 404 에러를 무시하지 않고 처리할 수 있도록 설정 (기본값 False 유지)
        'HTTPERROR_ALLOWED_CODES': [404] 
    }

    def parse(self, response):
        """
        공지사항 목록 페이지를 파싱하고 상세 페이지 요청을 생성합니다.
        """
        self.logger.debug(f"--- 현재 목록 페이지 크롤링: {response.url} ---")
        site_root = "https://www.cbnu.ac.kr"
        
        parsed_current_url = urlparse(response.url)
        current_query_params = parse_qs(parsed_current_url.query)
        
        bbs_no = current_query_params.get('bbsNo', ['8'])[0]
        board_key = current_query_params.get('key', ['813'])[0]
        
        should_stop_next_page = False
        
        # td.p-subject a를 포함하는 tr만 선택
        all_rows = response.css('td.p-subject a').xpath('ancestor::tr[1]')
        
        general_post_dates = []

        self.logger.debug(f"--- 발견된 게시글 행 수: {len(all_rows)} ---")


        for row in all_rows:
            link_selector = row.css('td.p-subject a')
            
            # 제목 추출 (상세 페이지에서 추출 실패를 방지하기 위해)
            title_from_list = link_selector.css('::text').get()
            if title_from_list:
                title_from_list = title_from_list.strip()
            
            # 날짜 추출 (6번째 td)
            date_td = row.xpath('./td[6]')
            raw_date_str = date_td.xpath('string(.)').get()
            
            date_only = None

            if raw_date_str:
                raw_date_str = raw_date_str.strip()
                self.logger.debug(f"--- [DEBUG LOG] Raw Extracted Date String from TD6: '{raw_date_str}' ---")
                
                # YYYY-MM-DD 패턴 정규 표현식 추출
                match = re.search(r'(\d{4}-\d{2}-\d{2})', raw_date_str)
                
                if match:
                    date_only = match.group(1)
                else:
                    self.logger.warning(f"--- [DEBUG LOG] Regex failed on TD6 string: '{raw_date_str}' ---")

            
            # 일반/공지 구분 로직
            is_sticky_post = 'p-notice' in row.attrib.get('class', '')
            is_general_post = not is_sticky_post


            # 날짜 파싱
            notice_date = None
            if date_only:
                try:
                    notice_date = datetime.strptime(date_only, '%Y-%m-%d').date()
                    
                    if is_general_post:
                        general_post_dates.append(notice_date)

                except ValueError:
                    self.logger.error(f"Failed to parse date string in list: ***'{raw_date_str}'*** (After Regex: '{date_only}'). Date parsing skipped for this row.")
            
            
            if link_selector:
                relative_url = link_selector.attrib['href']

                # --- 🚩 404 오류 해결을 위한 URL 절대 경로 생성 및 수정 로직 ---
                # response.urljoin을 사용하여 절대 URL을 생성합니다.
                full_url = response.urljoin(relative_url)
                
                # 만약 URL에 '/www/'가 없다면, 수동으로 삽입하여 404를 방지합니다.
                if '/www/' not in full_url:
                    full_url = full_url.replace(site_root + '/', site_root + '/www/')
                # --- 🚩 URL 수정 로직 끝 ---


                # URL에서 글 번호(nttNo) 추출 
                parsed_link_url = urlparse(full_url)
                query_params = parse_qs(parsed_link_url.query)
                ntt_no = query_params.get('nttNo', ['0'])[0]

                # 핵심 중복 요청 방지 로직
                if ntt_no != '0':
                    notice_key = f"{bbs_no}_{ntt_no}"

                    if notice_key in self.crawled_ntt_nos:
                        self.logger.debug(f"--- 🚫 중복 요청 건너뛰기: 이미 요청된 Notice Key={notice_key} ---")
                        continue
                    
                    self.crawled_ntt_nos.add(notice_key)

                    # 일반 게시물인 경우에만 중단 조건 확인
                    if is_general_post and notice_date and notice_date < self.STOP_DATE:
                        self.logger.info(f"--- 🛑 일반 게시물 날짜({notice_date}) 조건({self.STOP_DATE})에 도달: 다음 페이지 크롤링을 중단하지만, 이 글은 요청합니다. ---")
                        should_stop_next_page = True
                    
                    # 상세 페이지 요청
                    yield scrapy.Request(
                        url=full_url,
                        callback=self.parse_detail,
                        meta={
                            'notice_key': notice_key, 
                            'board_type': '전체공지',
                            'title': title_from_list, # 목록 제목 전달 (최종 제목으로 사용)
                            'post_date_from_list': notice_date # 목록 날짜 전달 (최종 날짜로 사용)
                        }
                    )
                else:
                    self.logger.warning(f"Could not find nttNo in URL: {full_url}")

        # --- 2. 다음 목록 페이지 링크 추출 ---
        
        self.logger.debug(f"--- 현재 페이지의 일반 게시물 날짜 목록: {general_post_dates} ---")
        
        current_page_index = int(current_query_params.get('pageIndex', ['1'])[0])
        
        if should_stop_next_page:
            self.logger.info(f"--- 🛑 중단 플래그 설정됨: 다음 페이지 크롤링 종료. ---")
        elif not general_post_dates and current_page_index > 1:
            self.logger.info("--- 🛑 일반 게시물 미발견 및 2페이지 이상: 유효 게시물이 없는 페이지로 간주하고 크롤링을 종료합니다. ---")
        else:
            # '다음' 버튼 유효성 검사 (목록 페이지의 '다음' 버튼이 존재하는지 확인)
            next_link = response.css('a.next').get()
            if next_link:
                next_page_index = current_page_index + 1
                
                next_url_params = f"bbsNo={bbs_no}&key={board_key}&pageIndex={next_page_index}"
                next_page_url = f"{site_root}/www/selectBbsNttList.do?{next_url_params}"
                
                self.logger.debug(f"--- 다음 페이지 ({next_page_index}) 요청: {next_page_url} ---")

                yield scrapy.Request(
                    url=next_page_url,
                    callback=self.parse,
                )
        

    def parse_detail(self, response):
        """
        개별 공지사항 상세 페이지를 파싱하여 Item을 반환합니다.
        """
        # 404 응답을 받았을 경우 처리를 건너뜁니다.
        if response.status == 404:
            self.logger.warning(f"--- ⚠️ 404 Not Found: URL 경로 오류로 이 게시물은 건너뜁니다. URL: {response.url} ---")
            return

        notice_key = response.meta.get('notice_key')
        board_type = response.meta.get('board_type')
        
        # 목록에서 전달받은 확정된 제목과 날짜를 사용합니다.
        title = response.meta.get('title')
        post_date = response.meta.get('post_date_from_list') 

        self.logger.debug(f"--- 상세 페이지 크롤링: {response.url} (Key: {notice_key}) ---")

        # --- 1. 본문 추출 (XPath 기반) ---
        # XPath: //*[@id="contents"]/div/div/div[2] 
        content_xpath = '//div[@id="contents"]/div/div/div[2]'
        
        raw_content_parts = response.xpath(f'{content_xpath}//text()').getall()
        
        # 텍스트 정리 및 결합 (불필요한 공백, 탭, 줄바꿈 제거)
        content = ' '.join(part.strip() for part in raw_content_parts if part.strip())
        
        # 만약 위 XPath로 추출이 안 된다면, 차선책으로 일반적인 콘텐츠 클래스를 시도합니다.
        if not content:
            content = response.css('.bbs_content').xpath('string(.)').get()
            if content:
                content = content.strip()


        # 최종 검증 및 반환
        if title and content and post_date:
            item = ChbNoticeItem()
            item['notice_id'] = notice_key
            item['title'] = title
            item['content'] = content
            item['url'] = response.url # <-- 키 이름을 'url'로 변경
            item['post_date'] = post_date
            item['board_type'] = board_type
            
            self.logger.debug(f"Scraped item success! Key: {notice_key} | Title: {title[:20]}... | Date: {post_date} | Content Length: {len(content)}")
            yield item
        else:
            self.logger.error(f"Failed to scrape essential fields for {notice_key}. Title: {title}, Content length: {len(content)}, Date: {post_date}. (This means XPath failed to find content)")