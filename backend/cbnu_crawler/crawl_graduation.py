#!/usr/bin/env python
"""졸업요건 페이지 크롤링"""

import os
import sys
import django

# 프로젝트 루트를 Python 경로에 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from chat.models import ChbNotice, NoticeRagIndex
from sentence_transformers import SentenceTransformer
from datetime import datetime
import time

print("🔍 졸업요건 페이지 크롤링...")
print("="*60)

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

print("📦 임베딩 모델 로딩...")
embedder = SentenceTransformer("jhgan/ko-sroberta-multitask")

graduation_urls = {
    '21학번': 'https://software.cbnu.ac.kr/sub0501/7594',
    '22학번': 'https://software.cbnu.ac.kr/sub0501/11631',
    '23학번': 'https://software.cbnu.ac.kr/sub0501/14714',
    '24학번': 'https://software.cbnu.ac.kr/sub0501/16401',
    '25학번': 'https://software.cbnu.ac.kr/sub0501/671048'
}

try:
    for year, url in graduation_urls.items():
        print(f"\n📌 [{year}] 크롤링...")
        print(f"   URL: {url}")
        
        try:
            driver.get(url)
            time.sleep(3)
            
            # 페이지 전체 텍스트 추출
            body = driver.find_element(By.TAG_NAME, 'body')
            content = body.text.strip()
            
            print(f"   내용 길이: {len(content)}자")
            
            # DB 저장
            notice, created = ChbNotice.objects.update_or_create(
                notice_id=f'sw_static_졸업요건_{year}',
                defaults={
                    'board_type': '소프트웨어학부-정적정보',
                    'title': f'졸업요건-{year}',
                    'content': content,
                    'source_url': url,
                    'post_date': datetime.now().date(),
                    'is_active': True
                }
            )
            
            # 임베딩 생성
            embedding = embedder.encode(content).tolist()
            
            # RAG 인덱스 저장
            NoticeRagIndex.objects.update_or_create(
                notice=notice,
                chunk_index=0,
                defaults={
                    'text': content,
                    'embedding': embedding
                }
            )
            
            print(f"   ✅ 저장 완료")
            
        except Exception as e:
            print(f"   ❌ 오류: {e}")
            continue
    
    print("\n" + "="*60)
    print("✅ 졸업요건 크롤링 완료!")
    print("="*60)
    
finally:
    driver.quit()
