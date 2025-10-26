# scrape_law.py에서 실행 안 되길래 만든 새 파일인데 이것도 안 됨(사법정보공개포털 로그인 이슈)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import os, sys, django

# Django 환경 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from data.cases.models import LawArticle

url = "https://portal.scourt.go.kr/pgp/main.on?w2xPath=PGP1021M04&jisCntntsSrno=3335773&srchwd=*&rnum=1&c=900&pgDvs=1"

options = Options()
options.add_argument("--headless")  # 창 안 띄우고 실행
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)
driver.get(url)

# 페이지 로딩 대기
time.sleep(5)

html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')
driver.quit()

articles = soup.find_all("div", class_="lawArticle")

print(f"총 {len(articles)}개 조문을 찾았습니다.")

for art in articles:
    num_tag = art.find(["strong", "b", "h4"])
    num = num_tag.get_text(strip=True) if num_tag else ""
    title = ""
    if "(" in num:
        title = num.split("(")[1].split(")")[0]
        num = num.split("(")[0]

    content_parts = [p.get_text(" ", strip=True) for p in art.find_all(["p", "li"]) if len(p.get_text(strip=True)) > 3]
    content = "\n".join(content_parts)

    if content:
        LawArticle.objects.create(
            law_name="지방세기본법",
            article_num=num,
            article_title=title,
            article_content=content
        )
        print(f"✅ {num} {title} 저장 완료")

print("🎉 모든 조문 저장 완료!")
