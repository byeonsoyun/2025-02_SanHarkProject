#!/usr/bin/env python
"""동아리 상세 정보 크롤링 - 각 동아리 클릭"""

import os
import django
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

print("🔍 동아리 상세 정보 크롤링...")
print("="*60)

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# 임베딩 모델 로드
print("📦 임베딩 모델 로딩...")
embedder = SentenceTransformer("jhgan/ko-sroberta-multitask")

try:
    driver.get('https://software.cbnu.ac.kr/sub040301')
    time.sleep(3)
    
    club_names = ['SAMMaru', 'CUVIC', 'PDA', 'EMSYS', 'Nest.net', 'NOVA', 'Tux']
    
    all_clubs_content = "소프트웨어학부 동아리 소개\n\n"
    
    for idx, club_name in enumerate(club_names):
        try:
            print(f"\n📌 [{club_name}] 크롤링...")
            
            # 동아리 탭 클릭
            tab_elem = driver.find_element(By.XPATH, f"//ul[@id='clubtab']/li[{idx+1}]")
            driver.execute_script("arguments[0].scrollIntoView(true);", tab_elem)
            time.sleep(0.5)
            tab_elem.click()
            time.sleep(1)
            
            # 해당 동아리의 contents 영역 찾기
            content_div = driver.find_element(By.ID, f"contents{idx+1}")
            
            # 동아리 정보 추출
            try:
                # 동아리장
                leader = content_div.find_element(By.XPATH, ".//th[contains(text(), '동아리장')]/following-sibling::td").text.strip()
            except:
                leader = ""
            
            try:
                # 지도교수
                professor = content_div.find_element(By.XPATH, ".//th[contains(text(), '지도교수')]/following-sibling::td").text.strip()
            except:
                professor = ""
            
            try:
                # 위치
                location = content_div.find_element(By.XPATH, ".//th[contains(text(), '위치')]/following-sibling::td").text.strip()
            except:
                location = ""
            

            
            try:
                # 동아리 소개
                intro = content_div.find_element(By.CSS_SELECTOR, "p.clubintro").text.strip()
            except:
                intro = ""
            
            try:
                # 주요활동 - ul.clublist의 모든 li
                activities_list = content_div.find_elements(By.CSS_SELECTOR, "ul.clublist li")
                activities = "\n".join([li.text.strip() for li in activities_list if li.text.strip()])
            except:
                activities = ""
            
            # 동아리 정보 조합
            club_info = f"\n{'='*60}\n"
            club_info += f"동아리명: {club_name}\n"
            if leader:
                club_info += f"동아리장: {leader}\n"
            if professor:
                club_info += f"지도교수: {professor}\n"
            if location:
                club_info += f"위치: {location}\n"
            if intro:
                club_info += f"\n[동아리 소개]\n{intro}\n"
            if activities:
                club_info += f"\n[주요활동 및 수상실적]\n{activities}\n"
            
            all_clubs_content += club_info
            
            print(f"   ✅ 수집 완료")
            
        except Exception as e:
            print(f"   ❌ 오류: {e}")
            continue
    
    print("\n" + "="*60)
    print("💾 DB 저장 중...")
    
    # DB 저장
    notice, created = ChbNotice.objects.update_or_create(
        notice_id='sw_static_커뮤니티_동아리소개_상세',
        defaults={
            'board_type': '소프트웨어학부-정적정보',
            'title': '커뮤니티-동아리소개',
            'content': all_clubs_content,
            'source_url': 'https://software.cbnu.ac.kr/sub040301',
            'post_date': datetime.now().date(),
            'is_active': True
        }
    )
    
    # 임베딩 생성
    print("🔄 임베딩 생성 중...")
    embedding = embedder.encode(all_clubs_content).tolist()
    
    # RAG 인덱스 저장
    NoticeRagIndex.objects.update_or_create(
        notice=notice,
        chunk_index=0,
        defaults={
            'text': all_clubs_content,
            'embedding': embedding
        }
    )
    
    print("✅ 저장 완료")
    print("\n" + "="*60)
    print("✅ 동아리 상세 정보 크롤링 완료!")
    print("="*60)
    print(f"📊 수집 결과:")
    print(f"   - 동아리 수: {len(club_names)}개")
    print(f"   - 총 내용 길이: {len(all_clubs_content)}자")
    print("="*60)
    
finally:
    driver.quit()
