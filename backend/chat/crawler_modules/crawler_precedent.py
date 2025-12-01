# backend/chat/crawler_modules/crawler_precedent.py

import requests
import json
from django.conf import settings
from .data_models import LawData 
from typing import List, Dict, Any

# --- 설정 및 상수 ---
SERVICE_KEY = getattr(settings, 'LAW_API_KEY', 'default_key')
OC_VALUE = 'qusthdbs1' 
API_URL = "https://www.law.go.kr/DRF/lawSearch.do"

# --- API 호출 함수: 판례 목록 조회 ---
def fetch_precedent_list(page_no: int = 1, display_count: int = 100) -> List[Dict[str, Any]]:
    """판례 목록을 페이지별로 JSON 형태로 조회하고 파싱합니다."""
    
    params = {
        'OC': OC_VALUE,                 
        'target': 'precSearch',         # 🚨 서비스 대상: precSearch 🚨
        'type': 'json',                 
        'query': '법',                  # 광범위 검색
        'display': display_count,       
        'page': page_no                 
    }
    
    # 판례는 데이터가 많아 응답이 느릴 수 있어 Timeout을 늘립니다.
    response = requests.get(API_URL, params=params, timeout=15) 
    print(f"API Response Status (판례): {response.status_code}")
    response.raise_for_status() 
    
    try:
        data = response.json()
        
        # 판례 API의 최상위 키는 'precSearch'입니다.
        main_data = data.get("precSearch", {}) 
        
        # 데이터 리스트 키는 '판례'로 가정합니다. (API 응답 확인 필요)
        precedent_list = main_data.get("판례", []) 
        total_count = int(main_data.get("검색결과개수", 0))

        for item in precedent_list:
            item['총건수'] = total_count

        return precedent_list

    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류 발생 (판례): {e}")
        return []
    except Exception as e:
        print(f"❌ 판례 목록 추출 중 오류 발생: {e}")
        return []

# --- 데이터 수집 및 정규화 함수 ---
def collect_and_normalize_precedents() -> List[LawData]:
    """모든 판례 데이터를 수집하고 LawData 스키마로 정규화합니다."""
    all_data: List[LawData] = []
    page = 1
    total_count = float('inf') 

    print("\n=== 판례 데이터 수집 시작 ===")

    while len(all_data) < total_count:
        try:
            list_items = fetch_precedent_list(page_no=page)
            
            if not list_items:
                # 데이터가 없거나 끝까지 도달
                break
            
            if page == 1 and list_items:
                total_count = int(list_items[0].get('총건수', 0)) 
                print(f"총 {total_count}건의 판례 목록 수집 예정.")

            for item in list_items:
                # 판례 API 필드명 (사건명, 판례일련번호, 판결요지 등 사용)
                precedent_id = str(item.get('판례일련번호', '')) 
                precedent_title = item.get('사건명', '')
                precedent_summary = item.get('판결요지', '') 
                
                if not precedent_id:
                    continue
                
                data = LawData(
                    document_id=f"PREC_{precedent_id}",
                    doc_type="판례",
                    title=precedent_title,
                    # 판결요지와 사건명을 결합하여 content로 사용
                    content=f"사건명: {precedent_title}. 판결요지: {precedent_summary}", 
                    source_url=f"https://www.law.go.kr/판례/{precedent_id}"
                )
                all_data.append(data)
                
            page += 1
            print(f"페이지 {page-1} 처리 완료. 현재 {len(all_data)}건 수집.")

        except Exception as e:
            print(f"판례 크롤링 중 오류 발생 (페이지 {page}): {e}")
            break
            
    print(f"=== 판례 데이터 수집 완료. 최종 {len(all_data)}건 ===")
    return all_data