# backend/chat/crawler_modules/crawler_law_rlt.py

import requests
import json
from django.conf import settings
from .data_models import LawData 
# 🚨 법령 ID 목록을 가져오는 헬퍼 함수가 필요합니다. 🚨
from .crawler_article_term_rlt import fetch_unique_law_ids
from typing import List, Dict, Any, Tuple

# --- 설정 및 상수 ---
SERVICE_KEY = getattr(settings, 'LAW_API_KEY', 'default_key')
OC_VALUE = 'qusthdbs1' 
API_URL = "https://www.law.go.kr/DRF/lawSearch.do" # 요청 URL: lawSearch.do

# --- API 호출 함수: 관련법령 조회 ---
def fetch_law_rlt(law_id: str) -> List[Dict[str, Any]]:
    """특정 법령에 연결된 관련법령 목록을 조회합니다."""
    
    params = {
        'OC': OC_VALUE,                 
        'target': 'lsRlt',               # 🚨 서비스 대상: lsRlt 🚨
        'type': 'json',                 
        'ID': law_id,                    # 법령 ID
    }
    
    response = requests.get(API_URL, params=params, timeout=15)
    
    try:
        response.raise_for_status() 
        data = response.json()
        
        main_data = data.get("lsRltSearch", {})
        law_list = main_data.get("법령", [])
        
        # 관련법령 정보는 law_list의 각 항목(법령) 내부에 있습니다.
        all_related_laws = []
        for law_data in law_list:
            related_laws = law_data.get("관련법령", [])
            base_law_id = law_data.get("기준법령ID", law_id)
            base_law_name = law_data.get("기준법령명", "")

            # 관련법령이 있을 경우 기준법령 정보를 추가
            for item in related_laws:
                cleaned_item = {}
                for key, value in item.items():
                    cleaned_item[key.strip()] = value 

                cleaned_item['기준법령ID'] = base_law_id
                cleaned_item['기준법령명'] = base_law_name
                all_related_laws.append(cleaned_item)
            
        return all_related_laws 

    except json.JSONDecodeError:
        return []
    except Exception as e:
        # print(f"❌ 관련법령 정보 추출 중 오류 발생: {e} (ID: {law_id})")
        return []

# --- 데이터 수집 및 정규화 함수 ---
# backend/chat/crawler_modules/crawler_law_rlt.py

def collect_and_normalize_law_rlt() -> List[LawData]:
    """모든 법령의 관련법령 연계 정보를 수집하고 LawData 스키마로 정규화합니다."""
    all_data: List[LawData] = []
    
    # 🚨 모든 법령 ID 목록을 가져옵니다. 🚨
    law_id_list = fetch_unique_law_ids()
    
    if not law_id_list:
        print("❌ 법령 ID 목록을 가져올 수 없어 관련법령 크롤링을 시작할 수 없습니다.")
        return []

    print(f"\n=== 관련법령 연계 데이터 수집 시작 (총 {len(law_id_list)}개 법령 순회) ===")

    for i, law_id in enumerate(law_id_list):
        # 🚨 수정: 루프 시작 시 base_law_name을 law_id로 초기화 🚨
        base_law_name = f"ID:{law_id}"
        
        try:
            rlt_list = fetch_law_rlt(law_id)
            
            # API 결과가 비어있지 않은 경우에만 내부 로직 실행
            if rlt_list:
                # 🚨 수정: rlt_list가 비어있지 않다면, 첫 번째 항목에서 실제 법령명을 추출하여 업데이트 🚨
                base_law_name = rlt_list[0]['기준법령명'] 

                for item in rlt_list:
                    # 🚨 LawData 스키마에 맞게 정규화 🚨
                    # base_law_name은 이제 루프가 돌면서 (rlt_list가 있다면) 실제 이름으로 할당됩니다.
                    # 첫 번째 항목에서 이미 추출했으므로 여기서 다시 할당할 필요는 없지만, 
                    # 안전을 위해 item에서 다시 가져옵니다.
                    current_base_law_name = item['기준법령명'] 
                    rlt_law_name = item['관련법령명']
                    rlt_code = item['법령간관계코드']
                    rlt_name = item['법령간관계']
                    
                    document_id = f"R_LL_{current_base_law_name}_{rlt_law_name}_{rlt_code}" 

                    content = (
                        f"'{current_base_law_name}'와 '{rlt_law_name}'는 '{rlt_name}' 관계(코드: {rlt_code})입니다. "
                        f"기준법령ID: {item.get('기준법령ID')}. 관련법령ID: {item.get('관련법령ID')}."
                    )
                    
                    data = LawData(
                        document_id=document_id,
                        doc_type="법령_법령_연계",
                        title=f"{current_base_law_name} - {rlt_name} - {rlt_law_name}",
                        content=content,
                        source_url=item.get('관련법령조회링크', '')
                    )
                    all_data.append(data)
            
            # rlt_list가 비어있어도 base_law_name은 f"ID:{law_id}"로 초기화되어 있으므로 오류 발생 방지
            if i % 100 == 99: # 100개 처리할 때마다 진행 상황 출력
                print(f"[{i + 1}/{len(law_id_list)}] {base_law_name} 관련법령 정보 처리 완료. 현재 {len(all_data)}건 수집.")


        except Exception as e:
            # 🚨 수정: 오류 로그에 base_law_name 사용 (초기화 덕분에 안전함) 🚨
            print(f"❌ 데이터 정규화 중 오류 발생 (법령: {base_law_name}): {e}")
            
    print(f"=== 관련법령 연계 데이터 수집 완료. 최종 {len(all_data)}건 ===")
    return all_data