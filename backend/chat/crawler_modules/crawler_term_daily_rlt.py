# backend/chat/crawler_modules/crawler_term_daily_rlt.py

import requests
import json
from django.conf import settings
from .data_models import LawData 
from .crawler_term import fetch_term_names # 🚨 기존 법령용어 크롤러에서 법령용어 이름을 가져오는 함수를 사용합니다. 🚨
from typing import List, Dict, Any

# --- 설정 및 상수 ---
SERVICE_KEY = getattr(settings, 'LAW_API_KEY', 'default_key')
OC_VALUE = 'qusthdbs1' 
API_URL = "https://www.law.go.kr/DRF/lawService.do" # 요청 URL 변경!

# --- API 호출 함수: 법령용어-일상용어 연계 조회 ---
def fetch_term_daily_rlt(term_name: str) -> List[Dict[str, Any]]:
    """특정 법령용어에 연결된 일상용어 목록을 조회합니다."""
    
    params = {
        'OC': OC_VALUE,                 
        'target': 'lstrmRlt',           # 서비스 대상: lstrmRlt
        'type': 'json',                 
        'query': term_name,             # 검색할 법령용어명
    }
    
    response = requests.get(API_URL, params=params, timeout=10)
    
    try:
        response.raise_for_status() 
        data = response.json()
        
        # 🚨 JSON 구조 분석 반영 🚨
        main_data = data.get("lstrmRltService", {})
        law_term_data = main_data.get("법령용어", {})
        
        # 실제 연계 리스트는 "연계용어" 키에 있습니다.
        related_terms_list = law_term_data.get("연계용어", []) 
        
        # 🚨🚨🚨 핵심 수정: 키에서 공백을 제거하고 필드를 정규화합니다. 🚨🚨🚨
        if related_terms_list:
            law_term_name = law_term_data.get("법령용어명", term_name)
            law_term_id = law_term_data.get("id", "N/A")
            
            cleaned_list = []
            for item in related_terms_list:
                cleaned_item = {}
                # 모든 키의 공백을 제거하고 새로운 딕셔너리에 저장
                for key, value in item.items():
                    cleaned_item[key.strip()] = value 

                # 연계 정보가 있다면, 법령용어명/ID를 각 항목에 추가 (키는 이미 정리됨)
                cleaned_item['법령용어명'] = law_term_name
                cleaned_item['법령용어id'] = law_term_id
                
                cleaned_list.append(cleaned_item)
            
            return cleaned_list # 정리된 리스트 반환

        return [] # 연계 정보가 없을 경우 빈 리스트 반환

    except json.JSONDecodeError:
        return []
    except Exception as e:
        # print(f"❌ 연계 정보 추출 중 오류 발생: {e} (용어: {term_name})")
        return []

# --- 데이터 수집 및 정규화 함수 ---
def collect_and_normalize_term_daily_rlt() -> List[LawData]:
    """모든 법령용어의 일상용어 연계 정보를 수집하고 LawData 스키마로 정규화합니다."""
    all_data: List[LawData] = []
    
    # 🚨 법령용어 목록을 가져와야 합니다. 🚨
    term_names = fetch_term_names() 
    
    if not term_names:
        print("❌ 법령용어 목록을 가져올 수 없어 연계 정보 크롤링을 시작할 수 없습니다.")
        return []

    print(f"\n=== 법령용어-일상용어 연계 데이터 수집 시작 (총 {len(term_names)}개 용어 순회) ===")

    for i, term_name in enumerate(term_names):
        try:
            rlt_list = fetch_term_daily_rlt(term_name)
            
            for item in rlt_list:
                # 🚨 LawData 스키마에 맞게 정규화 🚨
                law_name = item['법령용어명']
                daily_name = item['일상용어명']
                rlt_code = item['용어관계코드']
                rlt_name = item['용어관계']
                
                # 문서 ID는 법령용어명과 일상용어명을 결합하여 고유하게 생성
                document_id = f"R_TD_{law_name}_{daily_name}_{rlt_code}" 

                content = (
                    f"법령용어 '{law_name}'와 일상용어 '{daily_name}'의 관계: "
                    f"{rlt_name} (코드: {rlt_code}). "
                    f"법령용어 ID: {item.get('법령용어 id')}. "
                    f"일상용어 ID: {item.get('id')}."
                )
                
                data = LawData(
                    document_id=document_id,
                    doc_type="법령용어_일상용어_연계",
                    title=f"{law_name} - {rlt_name} - {daily_name}",
                    content=content,
                    source_url=item.get('용어간관계링크', '')
                )
                all_data.append(data)
                
            if i % 10 == 9: # 10개 처리할 때마다 진행 상황 출력
                print(f"[{i + 1}/{len(term_names)}] {law_name} 연계 정보 처리 완료. 현재 {len(all_data)}건 수집.")


        except Exception as e:
            print(f"❌ 데이터 정규화 중 오류 발생 (용어: {term_name}): {e}")
            
    print(f"=== 법령용어-일상용어 연계 데이터 수집 완료. 최종 {len(all_data)}건 ===")
    return all_data