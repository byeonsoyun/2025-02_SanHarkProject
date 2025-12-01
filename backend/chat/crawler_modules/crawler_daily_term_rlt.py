# backend/chat/crawler_modules/crawler_daily_term_rlt.py

import requests
import json
from django.conf import settings
from .data_models import LawData 
# 🚨 일상용어 목록을 가져오는 함수 임포트 🚨
from .crawler_daily_term import fetch_daily_term_names 
from typing import List, Dict, Any

# --- 설정 및 상수 (crawler_term_daily_rlt.py와 동일) ---
SERVICE_KEY = getattr(settings, 'LAW_API_KEY', 'default_key')
OC_VALUE = 'qusthdbs1' 
API_URL = "https://www.law.go.kr/DRF/lawService.do" 

# --- API 호출 함수: 일상용어-법령용어 연계 조회 ---
def fetch_daily_term_rlt(daily_term_name: str) -> List[Dict[str, Any]]:
    """특정 일상용어에 연결된 법령용어 목록을 조회합니다."""
    
    params = {
        'OC': OC_VALUE,                 
        'target': 'dlytrmRlt',           # 🚨 서비스 대상: dlytrmRlt 🚨
        'type': 'json',                 
        'query': daily_term_name,        # 검색할 일상용어명
    }
    
    response = requests.get(API_URL, params=params, timeout=10)
    
    try:
        response.raise_for_status() 
        data = response.json()
        
        main_data = data.get("dlytrmRltService", {})
        # 🚨 최상위 키가 "일상용어"로 바뀝니다. 🚨
        daily_term_data = main_data.get("일상용어", {})
        
        related_terms_list = daily_term_data.get("연계용어", []) 
        
        # 키의 공백을 제거하고 필드를 정규화하는 로직 추가
        if related_terms_list:
            daily_term_name_clean = daily_term_data.get("일상용어명", daily_term_name)
            daily_term_id = daily_term_data.get("id", "N/A")
            
            cleaned_list = []
            for item in related_terms_list:
                cleaned_item = {}
                for key, value in item.items():
                    cleaned_item[key.strip()] = value 

                cleaned_item['일상용어명'] = daily_term_name_clean
                cleaned_item['일상용어id'] = daily_term_id
                
                cleaned_list.append(cleaned_item)
            
            return cleaned_list 

        return [] 

    except json.JSONDecodeError:
        return []
    except Exception as e:
        # print(f"❌ 연계 정보 추출 중 오류 발생: {e} (용어: {daily_term_name})")
        return []

# --- 데이터 수집 및 정규화 함수 ---
def collect_and_normalize_daily_term_rlt() -> List[LawData]:
    """모든 일상용어의 법령용어 연계 정보를 수집하고 LawData 스키마로 정규화합니다."""
    all_data: List[LawData] = []
    
    # 🚨 일상용어 목록을 가져와야 합니다. 🚨
    term_names = fetch_daily_term_names() 
    
    if not term_names:
        print("❌ 일상용어 목록을 가져올 수 없어 연계 정보 크롤링을 시작할 수 없습니다.")
        return []

    print(f"\n=== 일상용어-법령용어 연계 데이터 수집 시작 (총 {len(term_names)}개 용어 순회) ===")

    for i, term_name in enumerate(term_names):
        try:
            rlt_list = fetch_daily_term_rlt(term_name)
            
            for item in rlt_list:
                # 🚨 LawData 스키마에 맞게 정규화 🚨
                daily_name = item['일상용어명']
                law_name = item['법령용어명'] # 법령용어명이 연계용어의 이름이 됩니다.
                rlt_code = item['용어관계코드']
                rlt_name = item['용어관계']
                
                document_id = f"R_DT_{daily_name}_{law_name}_{rlt_code}" 

                content = (
                    f"일상용어 '{daily_name}'와 법령용어 '{law_name}'의 관계: "
                    f"{rlt_name} (코드: {rlt_code}). "
                    f"일상용어 ID: {item.get('일상용어id')}. "
                    f"법령용어 ID: {item.get('id')}."
                )
                
                data = LawData(
                    document_id=document_id,
                    doc_type="일상용어_법령용어_연계", # 새로운 doc_type 정의
                    title=f"{daily_name} - {rlt_name} - {law_name}",
                    content=content,
                    source_url=item.get('용어간관계링크', '')
                )
                all_data.append(data)
                
            if i % 100 == 99: # 일상용어는 양이 많으므로 100개 처리할 때마다 출력
                print(f"[{i + 1}/{len(term_names)}] {daily_name} 연계 정보 처리 완료. 현재 {len(all_data)}건 수집.")


        except Exception as e:
            print(f"❌ 데이터 정규화 중 오류 발생 (용어: {term_name}): {e}")
            
    print(f"=== 일상용어-법령용어 연계 데이터 수집 완료. 최종 {len(all_data)}건 ===")
    return all_data