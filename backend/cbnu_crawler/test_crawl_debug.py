#!/usr/bin/env python
"""학부공지사항 크롤링 디버그"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
import time

print("🔍 디버그 모드 시작...")

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.implicitly_wait(10)

six_months_ago = datetime.now() - timedelta(days=180)
print(f"6개월 전 기준: {six_months_ago.strftime('%Y-%m-%d')}")

def parse_date(date_str):
    try:
        date_str = date_str.replace('.', '-').replace('/', '-').strip()
        return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        try:
            return datetime.strptime(f"{datetime.now().year}-{date_str}", '%Y-%m-%d')
        except:
            return None

try:
    driver.get('https://software.cbnu.ac.kr/sub0401')
    time.sleep(3)
    
    articles = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
    print(f"\n총 {len(articles)}개 게시글 발견\n")
    
    for idx, article in enumerate(articles[:15], 1):  # 처음 15개만
        try:
            # 제목
            title_elem = article.find_element(By.CSS_SELECTOR, 'a')
            title = title_elem.text.strip()
            
            # 날짜 - 여러 selector 시도
            date_str = None
            try:
                date_elem = article.find_element(By.CSS_SELECTOR, 'td.date')
                date_str = date_elem.text.strip()
            except:
                try:
                    # 마지막 td 시도
                    tds = article.find_elements(By.TAG_NAME, 'td')
                    if len(tds) > 0:
                        date_str = tds[-1].text.strip()
                except:
                    pass
            
            post_date = parse_date(date_str) if date_str else None
            
            # 6개월 체크
            is_recent = post_date and post_date >= six_months_ago if post_date else "날짜없음"
            
            print(f"{idx}. {title[:40]}...")
            print(f"   날짜 원본: '{date_str}'")
            print(f"   파싱결과: {post_date.strftime('%Y-%m-%d') if post_date else 'None'}")
            print(f"   6개월내: {is_recent}")
            print()
            
        except Exception as e:
            print(f"{idx}. 오류: {e}\n")
    
except Exception as e:
    print(f"오류: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()
