# backend/chat/crawler_modules/crawler_term_article_rlt.py

import requests
import json
from django.conf import settings
from .data_models import LawData 
from .crawler_term import fetch_term_names # 법령용어 목록 사용
from typing import List, Dict, Any
from typing import Tuple

# --- 설정 및 상수 ---
SERVICE_KEY = getattr(settings, 'LAW_API_KEY', 'default_key')
OC_VALUE = 'qusthdbs1' 
API_URL = "https://www.law.go.kr/DRF/lawService.do" # 요청 URL: lawService.do

# --- API 호출 함수: 법령용어-조문 연계 조회 ---
def fetch_term_article_rlt(term_name: str) -> List[Dict[str, Any]]:
    """특정 법령용어에 연결된 조문 목록을 조회합니다."""
    
    params = {
        'OC': OC_VALUE,                 
        'target': 'lstrmRltJo',           # 🚨 서비스 대상: lstrmRltJo 🚨
        'type': 'json',                 
        'query': term_name,             # 검색할 법령용어명
    }
    
    response = requests.get(API_URL, params=params, timeout=15)
    
    try:
        response.raise_for_status() 
        data = response.json()
        
        main_data = data.get("lstrmRltJoService", {})
        law_term_data = main_data.get("법령용어", {})
        
        # 실제 연계 리스트는 "연계법령" 키에 있습니다.
        related_articles_list = law_term_data.get("연계법령", []) 
        
        # 이전 API와 마찬가지로, 키의 공백을 제거하고 필드를 정규화하는 로직 추가
        if related_articles_list:
            law_term_name = law_term_data.get("법령용어명", term_name)
            law_term_id = law_term_data.get("id", "N/A")
            
            cleaned_list = []
            for item in related_articles_list:
                cleaned_item = {}
                for key, value in item.items():
                    # 키의 공백 제거
                    cleaned_item[key.strip()] = value 

                # 연계 정보 (법령용어명/ID)를 각 항목에 추가
                cleaned_item['법령용어명'] = law_term_name
                cleaned_item['법령용어id'] = law_term_id
                
                cleaned_list.append(cleaned_item)
            
            return cleaned_list 

        return [] 

    except json.JSONDecodeError:
        return []
    except Exception as e:
        # print(f"❌ 조문 연계 정보 추출 중 오류 발생: {e} (용어: {term_name})")
        return []

# --- 데이터 수집 및 정규화 함수 ---
def collect_and_normalize_term_article_rlt() -> List[LawData]:
    """모든 법령용어의 조문 연계 정보를 수집하고 LawData 스키마로 정규화합니다."""
    all_data: List[LawData] = []
    
    # 법령용어 목록을 가져옵니다.
    term_names = fetch_term_names() 
    
    if not term_names:
        print("❌ 법령용어 목록을 가져올 수 없어 조문 연계 정보 크롤링을 시작할 수 없습니다.")
        return []

    print(f"\n=== 법령용어-조문 연계 데이터 수집 시작 (총 {len(term_names)}개 용어 순회) ===")

    for i, term_name in enumerate(term_names):
        try:
            rlt_list = fetch_term_article_rlt(term_name)
            
            for item in rlt_list:
                # 🚨 LawData 스키마에 맞게 정규화 🚨
                law_name = item['법령용어명']
                article_title = item['법령명'] # 법령명이 조문의 상위 개념
                article_content = item['조문내용']
                article_no = item['조번호']
                
                # 문서 ID는 용어명, 법령명, 조번호를 결합하여 고유하게 생성
                document_id = f"R_TA_{law_name}_{article_title}_{article_no}" 

                content = (
                    f"법령용어 '{law_name}'가 '{article_title}' 제{article_no}조에 사용됨. "
                    f"조문내용 요약: {article_content[:150]}..." # 내용이 길 수 있으므로 요약
                )
                
                data = LawData(
                    document_id=document_id,
                    doc_type="법령용어_조문_연계", # 새로운 doc_type 정의
                    title=f"{law_name} - {article_title} 제{article_no}조",
                    content=content,
                    source_url=item.get('조문연계용어링크', '') # 조문-용어 연계 링크 사용
                )
                all_data.append(data)
                
            if i % 10 == 9: # 10개 처리할 때마다 진행 상황 출력
                print(f"[{i + 1}/{len(term_names)}] {law_name} 조문 연계 정보 처리 완료. 현재 {len(all_data)}건 수집.")


        except Exception as e:
            print(f"❌ 데이터 정규화 중 오류 발생 (용어: {term_name}): {e}")
            
    print(f"=== 법령용어-조문 연계 데이터 수집 완료. 최종 {len(all_data)}건 ===")
    return all_data

def fetch_article_query_list() -> List[Tuple[str, str, str]]:
    """
    LawDocument DB에서 유일한 조문 (법령 ID, 법령명, 조번호) 목록을 가져옵니다.
    이는 조문-법령용어 연계 크롤링의 쿼리 목록으로 사용됩니다.
    """
    try:
        from chat.models import LawDocument
        from django.db.models.functions import Substr, Cast
        from django.db.models import CharField, Value
        
        # '법령용어_조문_연계' 타입 데이터에서 조문 정보를 추출
        # LawDocument.title의 형태: "법령용어명 - 법령명 제조번호조"
        
        # LawDocument.content 필드에서 법령 ID, 조번호를 추출하는 것이 가장 이상적이지만,
        # 현재 content에 ID와 조번호가 명확히 분리되어 있지 않아,
        # DB에 저장된 'source_url' 필드에서 법령 ID와 조번호를 파싱하는 것이 안전합니다.
        
        # 임시 방안: 법령용어-조문 연계 데이터를 LawDocument 모델에서 추출합니다.
        # document_id 형태: R_TA_{law_name}_{article_title}_{article_no}
        
        # 모든 '법령용어_조문_연계' 데이터를 가져와 조문 정보만 중복 없이 추출합니다.
        all_rlt_data = LawDocument.objects.filter(doc_type="법령용어_조문_연계").all()
        
        article_set = set() # (law_id, law_name, jo_number_formatted)
        
        for doc in all_rlt_data:
            # source_url (조문연계용어링크) 형태: /DRF/lawService.do?OC=test&target=joRltLstrm&type=XML&ID=000243&JO=004200
            # 여기서 ID=000243 (법령 ID), JO=004200 (조번호)를 파싱합니다.
            
            source_url = doc.source_url
            if not source_url:
                continue

            # URL에서 파라미터 추출
            if "&ID=" in source_url and "&JO=" in source_url:
                law_id_part = source_url.split("&ID=")[1]
                law_id = law_id_part.split("&")[0]
                
                jo_number_part = source_url.split("&JO=")[1]
                jo_number = jo_number_part.split("&")[0]

                # title에서 법령명을 추출 (title: 법령용어 - 법령명 제조번호조)
                try:
                    law_name = doc.title.split(' - ')[1].split(' 제')[0].strip()
                except IndexError:
                    law_name = "알 수 없는 법령명"
                
                article_set.add((law_id, law_name, jo_number))
        
        if not article_set:
            print("🚨 경고: 조문 목록을 DB에서 찾을 수 없습니다. 법령용어-조문 연계 크롤링이 선행되어야 합니다.")
            
        return list(article_set)
        
    except Exception as e:
        print(f"❌ 조문 목록을 DB에서 가져오는 중 오류 발생: {e}")
        return []