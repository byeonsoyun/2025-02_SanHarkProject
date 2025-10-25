# scripts/elaw_parse_to_db.py
import os, re, glob
from bs4 import BeautifulSoup
import django, sys

# Django 세팅
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lawfriend.settings")
django.setup()

from data.cases.models import LawArticle

RAW_DIR = "data/elaw_raw"

# 조문 헤더 패턴 (제1조, 제2조 …)
ARTICLE_RE = re.compile(r"^제\s*\d+\s*조")

def extract_korean_side(html: str):
    """
    lawViewMultiContent.do는 국/영문 병기 구조.
    보통 한국어 쪽은 왼쪽 칼럼에 article들이 순서대로 들어있음.
    사이트 구조 변경 가능성이 있어 '제\d+조' 기준으로 잘라 저장.
    """
    soup = BeautifulSoup(html, "lxml")
    # 전체 텍스트 (태그 제외)로 일단 추출
    text = soup.get_text("\n", strip=True)

    # 법령명: header나 title에 들어있음
    title_tag = soup.find("title")
    law_name = title_tag.get_text(strip=True) if title_tag else "법령명 없음"

    # 라인별로 나눠서 '제x조'가 시작되는 위치를 찾아 구간으로 분리
    lines = [ln for ln in text.splitlines() if ln.strip()]
    articles = []
    idxs = []
    for i, ln in enumerate(lines):
        if ARTICLE_RE.match(ln):
            idxs.append(i)
    # 마지막 꼬리 처리
    idxs.append(len(lines))

    for a, b in zip(idxs[:-1], idxs[1:]):
        header = lines[a]
        body_lines = lines[a+1:b]
        # 제목이 괄호로 붙는 경우: "제1조(목적)"
        title = ""
        m = re.match(r"^(제\s*\d+\s*조)\s*(?:\((.*?)\))?", header)
        if m:
            art_no = m.group(1).replace(" ", "")
            title = m.group(2) or ""
        else:
            art_no = header.strip()
        body = "\n".join(body_lines).strip()
        if len(body) > 10:  # 너무 짧은 노이즈는 패스
            articles.append((art_no, title, body))
    return law_name, articles

def save_to_db(hseq: int, law_name: str, articles):
    for art_no, title, body in articles:
        LawArticle.objects.update_or_create(
            hseq=hseq,
            article_num=art_no,
            article_title=title,
            defaults={
                "law_name": law_name,
                "article_content": body,
            }
        )

def main():
    html_files = sorted(glob.glob(os.path.join(RAW_DIR, "*.html")))
    saved_cnt = 0
    for path in html_files:
        hseq = int(os.path.splitext(os.path.basename(path))[0])
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        law_name, articles = extract_korean_side(html)
        if not articles:
            continue
        save_to_db(hseq, law_name, articles)
        saved_cnt += 1
        if saved_cnt % 50 == 0:
            print(f"▶ {saved_cnt}개 파일 파싱 완료")

    print(f"✅ 파싱/저장 완료! 파일 수: {saved_cnt}")

if __name__ == "__main__":
    main()
