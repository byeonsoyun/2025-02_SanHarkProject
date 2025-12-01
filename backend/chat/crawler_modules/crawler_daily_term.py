# backend/chat/crawler_modules/crawler_daily_term.py

import requests
import json
from django.conf import settings
from .data_models import LawData 
from typing import List, Dict, Any

# --- 설정 및 상수 ---
SERVICE_KEY = getattr(settings, 'LAW_API_KEY', 'default_key')
OC_VALUE = 'qusthdbs1' 
API_URL = "https://www.law.go.kr/DRF/lawSearch.do"

# --- API 호출 함수: 일상용어 목록 조회 ---
def fetch_daily_term_list(page_no: int = 1, display_count: int = 100) -> List[Dict[str, Any]]:
    """일상용어 목록을 페이지별로 JSON 형태로 조회하고 파싱합니다."""
    
    params = {
        'OC': OC_VALUE,                 
        'target': 'dlytrm',             
        'type': 'json',                 
        'query': '법',                  
        'display': display_count,       
        'page': page_no                 
    }
    
    response = requests.get(API_URL, params=params, timeout=10)
    print(f"API Response Status (일상용어): {response.status_code}")
    response.raise_for_status() 
    
    # --- JSON 응답 처리 ---
    try:
        data = response.json()
        
        # 🚨 JSON 구조 확인 결과 반영 🚨
        main_data = data.get("dlytrmSearch", {}) 
        
        # 실제 데이터 리스트를 "일상용어" 키에서 가져옵니다.
        daily_term_list = main_data.get("일상용어", []) 
        
        # 총 건수는 "검색결과개수" 키에서 가져옵니다.
        total_count = int(main_data.get("검색결과개수", 0))

        # 디버깅: 데이터가 없는 경우
        if not daily_term_list and total_count > 0:
            print(f"❌ WARNING: '일상용어' 리스트를 찾지 못했지만, 총 {total_count}건이 확인됨. 파싱 키 문제.")
        
        # 총 건수 정보를 각 항목에 추가
        for item in daily_term_list:
            item['총건수'] = total_count

        return daily_term_list

    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류 발생 (일상용어): {e}")
        return []
    except Exception as e:
        print(f"❌ 일상용어 목록 추출 중 오류 발생: {e}")
        return []

# --- 데이터 수집 및 정규화 함수 ---
def collect_and_normalize_daily_terms() -> List[LawData]:
    """모든 일상용어 데이터를 수집하고 LawData 스키마로 정규화합니다."""
    all_data: List[LawData] = []
    page = 1
    total_count = float('inf') 

    print("\n=== 일상용어 데이터 수집 시작 ===")

    while len(all_data) < total_count:
        try:
            list_items = fetch_daily_term_list(page_no=page)
            
            if not list_items:
                break
            
            if page == 1 and list_items:
                # 총 건수 업데이트
                total_count = int(list_items[0].get('총건수', 0)) 
                # 페이지 당 100건, 205140건이므로 2052 페이지 필요
                print(f"총 {total_count}건의 일상용어 목록 수집 예정. (약 {total_count // 100 + 1} 페이지)") 

            for item in list_items:
                # 🚨 핵심 수정: 필드명 재확인 (공백 포함) 🚨
                daily_term_id = str(item.get('id', item.get('일상용어 id', ''))) # id 또는 일상용어 id 사용 
                daily_term_name = item.get('일상용어명', '')
                daily_term_source = item.get('출처', '') 
                
                if not daily_term_id:
                    continue
                
                data = LawData(
                    document_id=f"DLYTRM_{daily_term_id}",
                    doc_type="일상용어",
                    title=daily_term_name,
                    content=f"용어명: {daily_term_name}. 출처: {daily_term_source}", 
                    source_url=f"https://www.law.go.kr/일상용어/{daily_term_id}"
                )
                all_data.append(data)
                
            page += 1
            print(f"페이지 {page-1} 처리 완료. 현재 {len(all_data)}건 수집.")

        except Exception as e:
            print(f"일상용어 크롤링 중 오류 발생 (페이지 {page}): {e}")
            break
            
    print(f"=== 일상용어 데이터 수집 완료. 최종 {len(all_data)}건 ===")
    return all_data


def fetch_daily_term_names() -> List[str]:
    """
    용어 연계 크롤러가 쿼리할 수 있도록 
    DB에 저장된 일상용어 목록(이름)만 가져옵니다.
    """
    try:
        from chat.models import LawDocument
        
        # LawDocument 테이블에서 '일상용어' 타입의 모든 제목(title)을 가져옵니다.
        daily_term_names = list(LawDocument.objects.filter(doc_type="일상용어").values_list('title', flat=True))
        
        if not daily_term_names:
            print("🚨 경고: DB에서 '일상용어' 목록을 찾을 수 없습니다. 일상용어 크롤링을 먼저 실행해야 합니다.")
            
        return daily_term_names
        
    except ImportError:
        print("❌ DB 모델을 임포트할 수 없어 일상용어 이름 목록을 가져올 수 없습니다. 모델 정의 확인 필요.")
        return []
    except Exception as e:
        print(f"❌ 일상용어 이름 목록을 DB에서 가져오는 중 오류 발생: {e}")
        return []