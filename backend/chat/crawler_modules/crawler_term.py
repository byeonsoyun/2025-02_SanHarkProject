# backend/chat/crawler_modules/crawler_term.py

import requests
import json
from django.conf import settings
from .data_models import LawData # LawData 모델이 동일 디렉토리 또는 모듈에 있다고 가정
from typing import List, Dict, Any

# --- 설정 및 상수 ---
# settings.py에서 LAW_API_KEY를 로드했다고 가정
SERVICE_KEY = settings.LAW_API_KEY 
# OC 값: 사용자님의 이메일 ID 부분 (qusthdbs1@naver.com -> qusthdbs1)
OC_VALUE = 'qusthdbs1' 

API_URL = "https://www.law.go.kr/DRF/lawSearch.do"

# --- API 호출 함수: 법령용어 목록 조회 ---
def fetch_term_list(page_no: int = 1, display_count: int = 100) -> List[Dict[str, Any]]:
    """법령용어 목록을 페이지별로 JSON 형태로 조회하고 파싱합니다."""
    
    params = {
        'OC': OC_VALUE,                 # 사용자 이메일 ID
        'target': 'lstrmAI',            # 서비스 대상 (법령용어)
        'type': 'json',                 # 출력 형태 JSON
        'query': '법령',                # 검색 질의 (광범위하게 설정)
        'display': display_count,       # 페이지 당 결과 수
        'page': page_no                 # 현재 페이지
    }
    
    response = requests.get(API_URL, params=params, timeout=10)
    print(f"API Response Status: {response.status_code}")
    
    # 200 OK가 아닌 경우 오류 발생 (404, 401 등)
    response.raise_for_status() 
    
    # --- JSON 응답 처리 ---
    try:
        data = response.json()
        
        # 샘플 구조: {"lstrmAISearch": {...}}
        main_data = data.get("lstrmAISearch", {})
        
        # 데이터 추출 및 총 건수 확인
        term_list = main_data.get("법령용어", [])
        total_count = int(main_data.get("검색결과개수", 0))

        # 각 항목에 총 건수 정보를 추가 (Pagination 로직을 위해)
        for item in term_list:
            item['총건수'] = total_count

        return term_list

    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류 발생: {e}")
        # 디버깅을 위해 응답 텍스트의 앞부분 출력
        print(f"DEBUG: Response Text Start: {response.text[:200]}")
        return []
    except Exception as e:
        print(f"❌ 데이터 추출 중 오류 발생: {e}")
        return []

# --- 데이터 수집 및 정규화 함수 ---
def collect_and_normalize_terms() -> List[LawData]:
    """모든 법령용어 데이터를 수집하고 LawData 스키마로 정규화합니다."""
    all_data: List[LawData] = []
    page = 1
    total_count = float('inf') 

    print("=== 법령용어 데이터 수집 시작 ===")

    while len(all_data) < total_count:
        try:
            list_items = fetch_term_list(page_no=page)
            
            if not list_items:
                break
            
            # 첫 페이지에서만 총 건수 업데이트
            if page == 1 and list_items:
                # fetch_term_list에서 추가된 '총건수' 사용
                total_count = int(list_items[0].get('총건수', 0)) 
                print(f"총 {total_count}건의 법령용어 수집 예정.")

            for item in list_items:
                # JSON 샘플 키 사용
                term_id = str(item.get('id', '')) 
                term_name = item.get('법령용어명', '')
                term_remark = item.get('비고', '') 
                
                if not term_id:
                    continue
                
                # LawData 스키마에 맞춰 정규화
                data = LawData(
                    document_id=f"TERM_{term_id}",
                    doc_type="법령용어",
                    title=term_name,
                    content=f"용어명: {term_name}. 설명: {term_remark}", 
                    source_url=f"https://www.law.go.kr/법령용어/{term_id}"
                )
                all_data.append(data)
                
            page += 1
            print(f"페이지 {page-1} 처리 완료. 현재 {len(all_data)}건 수집.")

        except Exception as e:
            print(f"법령용어 크롤링 중 오류 발생 (페이지 {page}): {e}")
            break
            
    print(f"=== 법령용어 데이터 수집 완료. 최종 {len(all_data)}건 ===")
    return all_data

# ----------------------------------------------------------------------
# 🚨 새롭게 추가된 함수: 용어 연계 크롤러를 위한 법령용어 이름 목록 제공 🚨
# ----------------------------------------------------------------------

def fetch_term_names() -> List[str]:
    """
    용어 연계 크롤러가 쿼리할 수 있도록 
    DB에 저장된 법령용어 목록(이름)만 가져옵니다.
    """
    
    # DB에서 LawDocument 모델을 가져와야 하므로, 함수 내부에서 임포트합니다.
    try:
        from chat.models import LawDocument
        
        # LawDocument 테이블에서 '법령용어' 타입의 모든 제목(title)을 가져옵니다.
        term_names = list(LawDocument.objects.filter(doc_type="법령용어").values_list('title', flat=True))
        
        if not term_names:
            print("🚨 경고: DB에서 '법령용어' 목록을 찾을 수 없습니다. 법령용어 크롤링을 먼저 실행해야 합니다.")
            
        return term_names
        
    except ImportError:
        # chat.models가 정의되지 않았을 경우를 위한 처리
        print("❌ DB 모델을 임포트할 수 없어 법령용어 이름 목록을 가져올 수 없습니다. 모델 정의 확인 필요.")
        return []
    except Exception as e:
        print(f"❌ 법령용어 이름 목록을 DB에서 가져오는 중 오류 발생: {e}")
        return []