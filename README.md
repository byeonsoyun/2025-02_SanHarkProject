# 충북대학교 공지사항 챗봇 시스템 (CBNU Notice Chatbot)

충북대학교 학생들을 위한 AI 기반 공지사항 검색 및 학사일정 관리 챗봇 시스템입니다.

## 📋 주요 기능

### 1. 공지사항 검색
- **전체 공지사항**: 충북대 메인 홈페이지 공지사항 (1,950건)
- **학사일정**: 학사 일정 정보 (136건)
- **기숙사 정보**: 연락처, 위치, 식단, 공지사항 (128건)
- **학과 공지**: 소프트웨어학과 공지사항 (2건)

### 2. RAG 기반 검색
- pgvector를 활용한 의미 기반 검색
- 한국어 임베딩 모델 (jhgan/ko-sroberta-multitask)
- 총 2,215개 벡터 인덱스

### 3. 학사일정 관리
- Google Calendar 연동
- 일정 자동 추가 기능
- 학년도별 일정 구분 (2024/2025)

### 4. UI 기능
- 다크/라이트 모드 전환
- 멀티 채팅 세션 관리
- 실시간 대화 기록

## 🛠 기술 스택

### Backend
- **Framework**: Django 5.0
- **Database**: PostgreSQL (pgvector extension)
- **LLM**: Ollama (cbnu1 모델)
- **Crawler**: Scrapy + Selenium
- **Embedding**: Sentence-BERT (ko-sroberta-multitask)

### Frontend
- **Framework**: React 18
- **Styling**: Bootstrap + Custom CSS
- **State Management**: React Hooks

## 📦 설치 및 실행

### 1. 사전 요구사항
```bash
# Python 3.10+
python --version

# Node.js 16+
node --version

# PostgreSQL 14+ (pgvector extension)
psql --version

# Ollama
ollama --version
```

### 2. 데이터베이스 설정
```bash
# PostgreSQL 데이터베이스 생성
createdb cbnu_chatbot_db

# pgvector extension 설치
psql -d cbnu_chatbot_db -c "CREATE EXTENSION vector;"
```

### 3. Backend 설정
```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정 (.env 파일 생성)
cat > .env << EOF
DB_NAME=cbnu_chatbot_db
DB_USER=cbnu_user
DB_PASSWORD=1111
DB_HOST=localhost
DB_PORT=5432
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=cbnu1
EOF

# 데이터베이스 마이그레이션
python manage.py migrate

# 크롤링 실행 (공지사항 수집)
python manage.py run_crawler

# RAG 인덱스 구축
python manage.py run_rag_index
```

### 4. Frontend 설정
```bash
cd frontend

# 의존성 설치
npm install

# 환경변수 설정 (.env 파일 생성)
echo "REACT_APP_API_URL=http://localhost:8000" > .env
```

### 5. 시스템 실행
```bash
# 프로젝트 루트에서
cd scripts
./start_all.sh

# 또는 개별 실행
# Backend: cd backend && python manage.py runserver 8000
# Frontend: cd frontend && npm start
```

### 6. 접속
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/
- **Calendar**: http://localhost:3000/calendar

## 📁 프로젝트 구조

```
SanHark_CBNU/
├── backend/
│   ├── backend/              # Django 설정
│   ├── chat/                 # 챗봇 앱
│   │   ├── models.py        # 데이터 모델
│   │   ├── views.py         # API 엔드포인트
│   │   ├── services.py      # RAG 서비스
│   │   └── management/      # 관리 명령어
│   ├── cbnu_crawler/        # 크롤러
│   │   └── spiders/         # 크롤링 스파이더
│   └── requirements.txt     # Python 의존성
├── frontend/
│   ├── src/
│   │   ├── pages/          # 페이지 컴포넌트
│   │   │   ├── Chatbot.js  # 챗봇 페이지
│   │   │   └── CalendarPage.js
│   │   └── App.js          # 메인 앱
│   └── package.json        # Node 의존성
├── scripts/
│   ├── start_all.sh        # 시스템 시작
│   └── stop_all.sh         # 시스템 종료
└── logs/                   # 로그 파일
```

## 🔧 주요 명령어

### 크롤링
```bash
cd backend
source venv/bin/activate

# 전체 크롤링
python manage.py run_crawler

# 특정 스파이더만 실행
cd cbnu_crawler
scrapy crawl cbnu_notice    # 전체 공지
scrapy crawl calendar       # 학사일정
scrapy crawl dorm_final     # 기숙사
scrapy crawl software       # 소프트웨어학과
```

### RAG 인덱스 관리
```bash
# 전체 재구축
python manage.py run_rag_index

# 증분 업데이트
python manage.py run_rag_update
```

### 데이터베이스 초기화
```bash
# 스키마 리셋
python db_schema_reset.py

# 마이그레이션 재실행
python manage.py migrate
```

## 🎯 사용 예시

### 챗봇 질문 예시
```
# 공지사항 검색
"최근 장학금 공지 알려줘"
"소프트웨어학과 공지사항 보여줘"

# 학사일정 조회
"2025학년도 1학기 개강일이 언제야?"
"성적 확인 기간 알려줘"

# 기숙사 정보
"기숙사 연락처 알려줘"
"양성재 식단 보여줘"
"기숙사 공지사항 있어?"

# 일정 추가 (명시적 키워드 필요)
"중간고사 일정 추가해줘"
"개강일 캘린더에 추가해줘"
```

## 🔐 Google Calendar 연동 (선택사항)

1. Google Cloud Console에서 OAuth 2.0 클라이언트 생성
2. `credentials.json` 파일을 `backend/` 디렉토리에 저장
3. 첫 실행 시 브라우저에서 인증 진행

## 📊 데이터 현황

| 카테고리 | 데이터 수 | 업데이트 주기 |
|---------|----------|-------------|
| 전체공지 | 1,950건 | 수동 |
| 학사일정 | 136건 | 수동 |
| 기숙사 | 128건 | 수동 |
| 소프트웨어학과 | 2건 | 수동 |
| **RAG 인덱스** | **2,215건** | 크롤링 후 재구축 |

## 🐛 문제 해결

### 포트 충돌
```bash
# 사용 중인 포트 확인
lsof -i :8000  # Backend
lsof -i :3000  # Frontend

# 프로세스 종료
kill -9 <PID>
```

### 데이터베이스 연결 오류
```bash
# PostgreSQL 서비스 확인
pg_isready

# 데이터베이스 재시작
brew services restart postgresql  # macOS
sudo systemctl restart postgresql  # Linux
```

### Ollama 연결 오류
```bash
# Ollama 서비스 확인
ollama list

# 모델 다운로드
ollama pull cbnu1
```

## 📝 개발 참고사항

### 새로운 크롤러 추가
1. `backend/cbnu_crawler/cbnu_crawler/spiders/` 에 스파이더 생성
2. `ChbNoticeItem` 형식으로 데이터 반환
3. `board_type` 필드로 카테고리 구분

### RAG 시스템 커스터마이징
- `backend/chat/services.py` - RAGService 클래스
- 임베딩 모델 변경: `EMBEDDING_MODEL_NAME`
- 검색 결과 수 조정: `TOP_K`

## 👥 기여자

- 개발: SanHark Team
- 프로젝트: 2025-02 산학프로젝트

## 📄 라이선스

이 프로젝트는 교육 목적으로 개발되었습니다.
