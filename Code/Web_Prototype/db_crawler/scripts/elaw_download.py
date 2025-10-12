# scripts/elaw_download.py
import os, time, json, random, re
import requests

RAW_DIR = "data/elaw_raw"
os.makedirs(RAW_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/114.0 Safari/537.36"
}

def fetch_html(hseq: int) -> str:
    """국/영문 병기 본문 iframe 소스 HTML 가져오기"""
    url = f"https://elaw.klri.re.kr/kor_service/lawViewMultiContent.do?hseq={hseq}"
    r = requests.get(url, headers=HEADERS, timeout=20)
    # 200이 아니면 빈 문자열 리턴 (없는 hseq 가능)
    if r.status_code != 200:
        return ""
    return r.text

def already_downloaded(hseq: int) -> bool:
    return os.path.exists(os.path.join(RAW_DIR, f"{hseq}.html"))

def save_raw(hseq: int, html: str):
    path = os.path.join(RAW_DIR, f"{hseq}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

def main():
    # ✅ 수집 대상 hseq 목록: 범위/리스트 중 하나 선택
    # 1) 범위 예시: 68000 ~ 69000
    targets = list(range(68000, 69000))
    # 2) 또는 특정 리스트:
    # targets = [68565, 68566, 68567]

    ok, fail = 0, 0
    for i, hseq in enumerate(targets, 1):
        if already_downloaded(hseq):
            continue
        try:
            html = fetch_html(hseq)
            # 내용이 비정상적으로 짧으면 skip
            if len(html) < 1000:
                fail += 1
            else:
                save_raw(hseq, html)
                ok += 1
        except Exception as e:
            fail += 1
        # 예의상/차단 방지: 0.3~0.8초 랜덤 슬립
        time.sleep(random.uniform(0.3, 0.8))
        if i % 100 == 0:
            print(f"▶ 진행 {i}/{len(targets)}  저장 {ok}  실패 {fail}")
    print(f"✅ 완료! 저장 {ok}, 실패 {fail}")

if __name__ == "__main__":
    main()
