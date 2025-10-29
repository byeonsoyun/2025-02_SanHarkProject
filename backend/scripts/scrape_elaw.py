import os
import sys
import django
import requests
from bs4 import BeautifulSoup

# Django 환경 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lawfriend.settings')
django.setup()

from data.cases.models import LawArticle

def scrape_law(hseq=68565):
    url = f"https://elaw.klri.re.kr/kor_service/lawView.do?hseq={hseq}&lang=KOR"
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')

    # 법령 제목
    title_tag = soup.select_one("#lawNm, .lawTitle, h2")
    law_name = title_tag.get_text(strip=True) if title_tag else "법령명 없음"
    print(f"📘 {law_name}")

    # ✅ 조문 구간: #viewKOR 내부의 <div class="article"> 또는 <div class="lawView_content">
    main_area = soup.select_one("#viewKOR")
    if not main_area:
        print("❌ #viewKOR 영역을 찾지 못했습니다. HTML 구조가 변경된 것 같습니다.")
        print(soup.prettify()[:2000])  # 디버깅용
        return

    articles = main_area.find_all("div", class_="article")
    print(f"🔍 {len(articles)}개 조문 탐색됨")

    count = 0
    for art in articles:
        num_tag = art.find("strong", class_="artTitle")
        if not num_tag:
            continue

        num_text = num_tag.get_text(strip=True)
        article_num = num_text.split("(")[0].strip()
        article_title = ""
        if "(" in num_text:
            article_title = num_text.split("(")[1].split(")")[0]

        # 본문 내용: <p> 태그 안의 텍스트들
        content_parts = [p.get_text(" ", strip=True) for p in art.find_all("p")]
        article_content = "\n".join(content_parts).strip()

        if article_content:
            LawArticle.objects.create(
                law_name=law_name,
                article_num=article_num,
                article_title=article_title,
                article_content=article_content
            )
            count += 1
            print(f"✅ {article_num} 저장 완료")

    print(f"🎉 총 {count}개 조문 저장 완료!")


if __name__ == "__main__":
    scrape_law(hseq=68565)
