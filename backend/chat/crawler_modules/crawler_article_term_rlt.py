# backend/chat/crawler_modules/crawler_article_term_rlt.py

import requests
import json
from django.conf import settings
from .data_models import LawData 
from typing import List, Dict, Any, Tuple

# 🚨 조문 ID/번호 쌍을 가져오는 헬퍼 함수가 필요합니다. 🚨
from .crawler_term_article_rlt import fetch_article_query_list

# --- 설정 및 상수 ---
SERVICE_KEY = getattr(settings, 'LAW_API_KEY', 'default_key')
OC_VALUE = 'qusthdbs1' 
API_URL = "https://www.law.go.kr/DRF/lawService.do" 

# --- API 호출 함수: 조문-법령용어 연계 조회 ---
def fetch_article_term_rlt(law_id: str, jo_number: str) -> List[Dict[str, Any]]:
    """특정 조문에 연결된 법령용어 목록을 조회합니다."""
    
    params = {
        'OC': OC_VALUE,                 
        'target': 'joRltLstrm',           # 🚨 서비스 대상: joRltLstrm 🚨
        'type': 'json',                 
        'ID': law_id,                    # 법령 ID
        'JO': jo_number                  # 조번호 (예: 000400)
    }
    
    response = requests.get(API_URL, params=params, timeout=15)
    
    try:
        response.raise_for_status() 
        data = response.json()
        
        main_data = data.get("joRltLstrmService", {})
        article_data = main_data.get("법령조문", {})
        
        # 실제 연계 리스트는 "연계용어" 키에 있습니다.
        related_terms_list = article_data.get("연계용어", []) 
        
        if related_terms_list:
            law_name = article_data.get("법령명", "")
            jo_no_raw = article_data.get("조번호", "") # 0004
            jo_gaji_no = article_data.get("조가지번호", "00") # 00
            
            cleaned_list = []
            for item in related_terms_list:
                cleaned_item = {}
                for key, value in item.items():
                    # 키의 공백 제거
                    cleaned_item[key.strip()] = value 

                # 연계 정보 (조문 정보)를 각 항목에 추가
                cleaned_item['법령명'] = law_name
                cleaned_item['조번호'] = jo_no_raw
                cleaned_item['조가지번호'] = jo_gaji_no
                
                cleaned_list.append(cleaned_item)
            
            return cleaned_list 

        return [] 

    except json.JSONDecodeError:
        return []
    except Exception as e:
        # print(f"❌ 조문-용어 연계 정보 추출 중 오류 발생: {e} (ID: {law_id}, JO: {jo_number})")
        return []

# --- 데이터 수집 및 정규화 함수 ---
def collect_and_normalize_article_term_rlt() -> List[LawData]:
    """모든 조문의 법령용어 연계 정보를 수집하고 LawData 스키마로 정규화합니다."""
    all_data: List[LawData] = []
    
    # 🚨 '법령용어-조문 연계' 크롤링 결과에서 유일한 조문 목록을 가져옵니다. 🚨
    # 구조: List[Tuple[law_id, law_name, jo_number_formatted]]
    article_query_list = fetch_article_query_list()
    
    if not article_query_list:
        print("❌ 조문 목록을 가져올 수 없어 조문-법령용어 연계 크롤링을 시작할 수 없습니다. 법령용어-조문 연계 크롤링을 먼저 실행해야 합니다.")
        return []

    print(f"\n=== 조문-법령용어 연계 데이터 수집 시작 (총 {len(article_query_list)}개 조문 순회) ===")

    for i, (law_id, law_name, jo_number) in enumerate(article_query_list):
        try:
            rlt_list = fetch_article_term_rlt(law_id, jo_number)
            
            for item in rlt_list:
                # 🚨 LawData 스키마에 맞게 정규화 🚨
                term_name = item['법령용어명']
                jo_no_raw = item['조번호']
                jo_gaji_no = item['조가지번호']
                
                # 문서 ID는 법령명, 조번호, 용어명을 결합하여 고유하게 생성
                document_id = f"R_AT_{law_id}_{jo_number}_{term_name}" 

                content = (
                    f"'{law_name}' 제{jo_no_raw}조({jo_gaji_no})에 사용된 법령용어: '{term_name}'. "
                    f"용어구분: {item.get('용어구분')} (코드: {item.get('용어구분코드')}). "
                )
                
                data = LawData(
                    document_id=document_id,
                    doc_type="조문_법령용어_연계", # 새로운 doc_type 정의
                    title=f"{law_name} 제{jo_no_raw}조 - {term_name}",
                    content=content,
                    source_url=item.get('용어연계조문링크', '')
                )
                all_data.append(data)
                
            if i % 100 == 99: # 100개 처리할 때마다 진행 상황 출력
                print(f"[{i + 1}/{len(article_query_list)}] {law_name} 제{jo_no_raw}조 연계 정보 처리 완료. 현재 {len(all_data)}건 수집.")


        except Exception as e:
            print(f"❌ 데이터 정규화 중 오류 발생 (법령: {law_name}, 조: {jo_number}): {e}")
            
    print(f"=== 조문-법령용어 연계 데이터 수집 완료. 최종 {len(all_data)}건 ===")
    return all_data

def fetch_unique_law_ids() -> List[str]:
    """
    LawDocument DB에서 유일한 법령 ID 목록을 가져옵니다. 
    이는 관련법령 크롤링의 쿼리 목록으로 사용됩니다.
    """
    
    # 🚨 fetch_article_query_list를 재활용합니다. 🚨
    # fetch_article_query_list의 결과: List[Tuple[law_id, law_name, jo_number]]
    article_list = fetch_article_query_list()
    
    if not article_list:
        return []
        
    # 첫 번째 요소(law_id)만 추출하여 Set으로 중복을 제거한 후 List로 반환
    law_ids = list(set([item[0] for item in article_list]))
    
    return law_ids