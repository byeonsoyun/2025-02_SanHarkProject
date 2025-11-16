import requests
import pandas as pd
import xml.etree.ElementTree as ET
from tqdm import tqdm # 진행률 표시를 위한 라이브러리
import time

# 🚨🚨🚨 Step A: 법제처에서 확인한 정확한 OC 코드로 교체! 🚨🚨🚨
id = "qusthdbs1" 
keyword = "공무원"

# base_url 정의
base_url = (
    f"https://www.law.go.kr/DRF/lawSearch.do?OC={id}" # HTTPS 사용 권장
    "&target=prec&type=XML" # 판례(prec)를 XML 형식으로 요청
    f"&query={keyword}" # "공무원" 키워드
    "&display=100" # 한 번에 100개씩
    "&prncYd=20000101~20231231" # 2000년부터 2023년까지 (파라미터명 '=' 수정)
    "&search=2" # 판시요지와 판시내용 검색
)

# 1. 총 검색 건수 확인
res = requests.get(base_url)
# 🚨🚨🚨 빈 응답 방지를 위한 기본 검증 추가 🚨🚨🚨
if not res.text.strip().startswith('<?xml'):
    print("❌ 오류: 서버가 유효한 XML을 반환하지 않았습니다. 키를 다시 확인하세요.")
    print(f"서버 응답 내용 시작: {res.text.strip()[:100]}...")
    totalCnt = 0 # 0으로 설정하여 수집 루프를 건너뜀
else:
    xtree = ET.fromstring(res.text)
    totalCnt = int(xtree.find('totalCnt').text)
    print(f"🔍 총 검색된 판례 갯수: {totalCnt}개")

# 2. 데이터 수집 루프
rows = []
if totalCnt > 0:
    # 요청 횟수 계산 (100개씩 가져오므로)
    num_requests = int(totalCnt // 100) + 2 
    
    for page in tqdm(range(1, num_requests)):
        url = f"{base_url}&page={page}"
        response = requests.get(url)
        
        # 🚨 응답이 유효한 XML일 경우에만 파싱
        if response.text.strip().startswith('<?xml'):
            xtree = ET.fromstring(response.text) 
        else:
            print(f"\n❌ 페이지 {page}에서 XML 응답 실패. 반복 중단.")
            break
            
        try:
            # 데이터가 들어있는 노드부터 시작 (XML 구조에 따라 5번째 노드부터 시작)
            items = xtree[5:] 
        except:
            break

        for node in items:
            # 안전하게 데이터 추출 (NoneType 오류 방지)
            data = {}
            for tag in ["판례일련번호", "사건명", "사건번호", "선고일자", "법원명", "사건종류명", "사건종류코드", "판결유형", "선고", "판례상세링크"]:
                element = node.find(tag)
                data[tag] = element.text if element is not None else "N/A"
            rows.append(data)
            
        time.sleep(0.5) # 서버 부하 방지를 위한 딜레이

# 3. 데이터프레임 변환 및 저장
if rows:
    df = pd.DataFrame(rows)
    output_filename = f'{keyword}_판례_{len(df)}개.csv'
    df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    
    print("\n--- 수집된 최종 데이터 (상위 5개) ---")
    print(df.head())
    print(f"\n✅ 성공! '{output_filename}' 파일이 로컬 PC에 저장되었습니다.")
else:
    print("\n데이터 수집에 실패했거나 총 검색 건수가 0입니다.")