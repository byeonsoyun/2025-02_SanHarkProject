



import os
import sys
import django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Django 프로젝트 환경 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()
import requests
from bs4 import BeautifulSoup




from data.cases.models import LawArticle

# 대상 URL
url = "https://portal.scourt.go.kr/pgp/main.on?w2xPath=PGP1021M04&jisCntntsSrno=3335773&srchwd=*&rnum=1&c=900&pgDvs=1"

# HTML 요청
res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
res.encoding = 'utf-8'
soup = BeautifulSoup(res.text, 'html.parser')

# 법령 이름
law_name = "지방세기본법"

# 각 조문(제1조, 제2조 등) 찾기
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
            law_name=law_name,
            article_num=num,
            article_title=title,
            article_content=content
        )
        print(f"✅ {num} {title} 저장 완료")

print("🎉 모든 조문 저장 완료!")
print(soup.prettify()[:1500])

