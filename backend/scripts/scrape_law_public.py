# 로그인이 필요 없는 사이트 크롤링이라해서 해보려 했는데 안 됨 
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from django.conf import settings
import os
import sys
import django

# -----------------------------
# Django 환경 설정
# -----------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from data.cases.models import LawArticle

# -----------------------------
# Selenium Chrome 옵션
# -----------------------------
chrome_options = Options()
chrome_options.add_argument("--headless")  # 필요 시 GUI 없이 실행
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--window-size=1920,1080")

driver_path = "C:/drivers/chromedriver-win64/chromedriver.exe"  # 본인 크롬드라이버 경로
service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# -----------------------------
# 대상 URL
# -----------------------------
url = "https://portal.scourt.go.kr/pgp/main.on?w2xPath=PGP1021M04&jisCntntsSrno=3335773&srchwd=*&rnum=1&c=900&pgDvs=1"
driver.get(url)
time.sleep(5)  # 페이지 로딩 대기

# -----------------------------
# iframe 확인 후 접근
# -----------------------------
iframes = driver.find_elements(By.TAG_NAME, "iframe")
print(f"총 {len(iframes)}개의 iframe 발견")

for i, frame in enumerate(iframes):
    driver.switch_to.frame(frame)
    print(f"{i}번 iframe 접근")

    # 조문 div 찾기
    articles = driver.find_elements(By.CSS_SELECTOR, "div.lawcon p")
    print(f"{i}번 iframe에서 {len(articles)}개 조문 발견")

    for art in articles:
        try:
            text = art.text.strip()
            label_tag = art.find_element(By.TAG_NAME, "label")
            num_title = label_tag.text.strip() if label_tag else ""

            # num / title 분리
            if "(" in num_title:
                num = num_title.split("(")[0].strip()
                title = num_title.split("(")[1].replace(")", "").strip()
            else:
                num = num_title
                title = ""

            if text:
                LawArticle.objects.create(
                    law_name="지방세기본법",
                    article_num=num,
                    article_title=title,
                    article_content=text
                )
                print(f"✅ {num} {title} 저장 완료")
        except Exception as e:
            print("⚠️ 오류 발생:", e)

    driver.switch_to.default_content()  # iframe 밖으로 나옴

driver.quit()
print("🎉 모든 조문 저장 완료!")
