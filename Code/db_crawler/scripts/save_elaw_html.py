from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=chrome_options)

# 메인 페이지 (iframe이 포함된 페이지)
url = "https://elaw.klri.re.kr/kor_service/lawView.do?hseq=68565&lang=KOR"
driver.get(url)
time.sleep(5)

# ✅ 1. 본문 iframe으로 진입
iframe = driver.find_element("id", "lawViewContent")
driver.switch_to.frame(iframe)
time.sleep(2)

# ✅ 2. iframe 안의 HTML 가져오기
html = driver.page_source

# ✅ 3. 저장
with open("elaw_page.html", "w", encoding="utf-8") as f:
    f.write(html)

driver.quit()
print("✅ elaw_page.html 저장 완료 (본문 iframe 내부 포함)")
