import os
import sys
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import django

# ✅ Django 설정 로드
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lawfriend.settings")
django.setup()

from cases.models import LawArticle

# ✅ 저장 경로 설정
SAVE_DIR = "data/elaw_raw"
os.makedirs(SAVE_DIR, exist_ok=True)

# ✅ Selenium 기본 설정
chrome_options = Options()
chrome_options.add_argument("--headless")  # 브라우저 창 숨기기
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=chrome_options)

# ✅ 수집할 법령 번호 범위 (테스트 범위)
START_ID = 68565
END_ID = 68700   # ⚠️ 테스트는 100~200개만 먼저

print(f"\n📘 [법령 자동 수집 시작] 범위: {START_ID} ~ {END_ID}\n")

for hseq in range(START_ID, END_ID):
    url = f"https://elaw.klri.re.kr/kor_service/lawViewMultiContent.do?hseq={hseq}"
    print(f"🔍 수집 중: {url}")

    try:
        driver.get(url)

        # ✅ 조문(.article)이 로드될 때까지 최대 10초 대기
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".article"))
            )
        except:
            print(f"⏳ {hseq} 페이지 로딩 대기 초과 (조문 없음)")
            continue

        html = driver.page_source
        file_path = os.path.join(SAVE_DIR, f"{hseq}.html")

        # ✅ HTML 백업 저장
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)

        # ✅ BeautifulSoup 파싱
        soup = BeautifulSoup(html, "lxml")

        # 법령명 추출
        law_name_el = soup.select_one("div.tit > strong")
        law_name = law_name_el.get_text(strip=True) if law_name_el else None

        # 조문 블록 추출
        article_blocks = soup.select(".article")

        # ✅ 예외 처리: 법령명 또는 조문이 없으면 스킵
        if not law_name or not article_blocks:
            print(f"⚠️ {hseq} 법령명 또는 조문 없음 — 저장 안 함")
            continue

        # ✅ DB 저장
        saved_count = 0
        for a in article_blocks:
            num_el = a.select_one(".articleTitleNum")
            title_el = a.select_one(".articleTitle")
            content_el = a.select_one(".articleTxt")

            article_num = num_el.get_text(strip=True) if num_el else ""
            article_title = title_el.get_text(strip=True) if title_el else ""
            article_content = content_el.get_text(strip=True) if content_el else ""

            LawArticle.objects.update_or_create(
                law_name=law_name,
                article_num=article_num,
                defaults={
                    "article_title": article_title,
                    "article_content": article_content,
                },
            )
            saved_count += 1

        print(f"✅ {hseq} 저장 완료 ({law_name}, 조문 {saved_count}개)")

    except Exception as e:
        print(f"❌ {hseq} 처리 중 오류 발생: {e}")
        continue

driver.quit()
print("\n🎉 모든 법령 자동 수집 및 DB 저장 완료!")
