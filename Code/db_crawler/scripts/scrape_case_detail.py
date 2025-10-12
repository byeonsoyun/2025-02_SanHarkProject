import os, sys, re, requests
from bs4 import BeautifulSoup

# Django 환경 로드
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lawfriend.settings')
import django
django.setup()

from cases.models import CaseLaw

# ========================
# 대법원 판례 상세 페이지 크롤링
# ========================

URL = "https://glaw.scourt.go.kr/wsjo/panre/sjo100.do?contId=202307000"
# ↑ 여기에 실제 판례 상세 URL 넣기
# 예시) https://glaw.scourt.go.kr/wsjo/panre/sjo100.do?contId=202307000 같은 형태

def fetch_case_detail(url):
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, "html.parser")

    # 제목, 사건번호, 선고일자
    title_tag = soup.select_one(".s_title, .title, h2")
    title = title_tag.get_text(strip=True) if title_tag else "제목없음"

    # 사건정보: "대법원 2025. 7. 24. 선고 2023다240299 전원합의체 판결"
    info_line = title

    # 텍스트 전체 가져오기
    main = soup.select_one("#content, .contArea, .law-detail, .view-cont, .contents")
    full_text = main.get_text("\n", strip=True) if main else soup.get_text("\n", strip=True)

    # 항목별 추출 (판시사항 / 판결요지 / 참조조문 / 참조판례)
    sections = {}
    for tag in soup.select("div, h3, strong, b"):
        txt = tag.get_text(strip=True)
        if txt in ["판시사항", "판결요지", "참조조문", "참조판례", "이유"]:
            next_div = tag.find_next_sibling("div")
            if next_div:
                sections[txt] = next_div.get_text("\n", strip=True)

    # 기본 정보 파싱
    m = re.search(r"(대법원)\s*(\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.)\s*선고\s*([0-9가-힣]+)\s*판결", info_line)
    if m:
        court_name, judgment_date, case_number = m.groups()
    else:
        court_name, judgment_date, case_number = "대법원", "", ""

    # DB 저장
    case = CaseLaw.objects.create(
        case_title=title,
        court_name=court_name,
        judgment_date=judgment_date,
        case_number=case_number,
        content_summary=sections.get("판결요지", ""),
        full_text=full_text,
        references="\n".join(f"{k}: {v}" for k, v in sections.items())
    )
    print(f"✅ {case.case_title} 저장 완료")

if __name__ == "__main__":
    fetch_case_detail(URL)
    print("🎉 모든 데이터 저장 완료!")
