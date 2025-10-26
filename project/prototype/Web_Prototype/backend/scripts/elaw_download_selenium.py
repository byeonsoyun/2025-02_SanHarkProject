# scripts/elaw_download_selenium.py
import os, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

RAW_DIR = "data/elaw_raw"
os.makedirs(RAW_DIR, exist_ok=True)

def fetch_with_selenium(hseq: int):
    url = f"https://elaw.klri.re.kr/kor_service/lawViewMultiContent.do?hseq={hseq}"

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    time.sleep(4)
    html = driver.page_source
    driver.quit()
    path = os.path.join(RAW_DIR, f"{hseq}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Selenium으로 저장: {path}")

if __name__ == "__main__":
    fetch_with_selenium(68565)
