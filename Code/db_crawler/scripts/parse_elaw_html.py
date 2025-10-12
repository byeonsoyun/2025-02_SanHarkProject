from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# 셀레니움 옵션 설정
chrome_options = Options()
chrome_options.add_argument("--headless")  # 브라우저 창 안 띄움
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# 크롬 드라이버 실행 (PATH는 자동 인식됨)
driver = webdriver.Chrome(options=chrome_options)

# ✅ 조문이 실제 들어 있는 페이지 주소
url = "https://elaw.klri.re.kr/kor_service/lawViewMultiContent.do?hseq=68565"

# 페이지 열기
driver.get(url)
time.sleep(5)  # JS 로딩 대기

# 페이지 전체 HTML 가져오기
html = driver.page_source

# HTML 저장
with open("elaw_page.html", "w", encoding="utf-8") as f:
    f.write(html)

driver.quit()
print("✅ elaw_page.html 저장 완료!")
