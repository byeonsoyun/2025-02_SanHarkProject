# 🎓 SanHark CBNU - 충북대학교 AI 챗봇 시스템

충북대학교 학생들을 위한 AI 기반 통합 정보 제공 및 일정 관리 챗봇 시스템

## 📋 목차
- [주요 기능](#주요-기능)
- [시스템 구조](#시스템-구조)
- [설치 및 실행](#설치-및-실행)
- [기술 스택](#기술-스택)
- [API 엔드포인트](#api-엔드포인트)

---

## 🎯 주요 기능

### 1. AI 챗봇 (RAG 기반)
- **충북대 공지사항 검색**: 학교, 학부, 기숙사 공지사항 실시간 검색
- **소프트웨어학부 정보**: 학부 공지, 교과과정, 졸업요건 등 상세 정보 제공
- **자연어 대화**: 한국어 자연어 처리를 통한 직관적인 질의응답
- **컨텍스트 기반 응답**: 대화 맥락을 이해하고 연관된 정보 제공

### 2. 일정 관리
- **로컬 일정 관리**: 사용자별 일정 추가, 조회, 삭제
- **구글 캘린더 연동**: OAuth 2.0 기반 구글 캘린더 동기화
- **자동 일정 추출**: 대화에서 일정 정보 자동 추출 및 등록
- **학사일정 통합**: 충북대 학사일정 자동 크롤링 및 제공

### 3. 데이터 크롤링
- **정기 크롤링** (Scrapy 프레임워크)
  - 학사일정 (calendar_spider)
  - 학교 공지사항 (cbnu_notice_spider)
  - 기숙사 공지사항 (dorm_final_spider)
  
- **일회성 크롤링** (Selenium)
  - 소프트웨어학부 상세 정보
  - 졸업요건 정보
  - 동아리 정보

---

## 🏗️ 시스템 구조

```
SanHark_CBNU/
├── backend/                    # Django 백엔드
│   ├── backend/               # Django 설정
│   │   ├── settings.py       # 프로젝트 설정
│   │   ├── urls.py           # URL 라우팅
│   │   └── wsgi.py           # WSGI 설정
│   │
│   ├── chat/                  # 챗봇 앱
│   │   ├── models.py         # DB 모델 (ChatMessage, ChbNotice, UserEvent 등)
│   │   ├── views.py          # API 뷰 (채팅, 일정 관리)
│   │   ├── services.py       # RAG 서비스 (벡터 검색, LLM 통합)
│   │   ├── google_calendar_service.py  # 구글 캘린더 연동
│   │   └── management/       # Django 관리 명령어
│   │       └── commands/
│   │           ├── run_crawler.py      # 크롤러 실행
│   │           ├── run_rag_index.py    # RAG 인덱싱
│   │           └── run_rag_update.py   # RAG 업데이트
│   │
│   ├── api/                   # API 앱
│   ├── user_mgmt/            # 사용자 관리 앱
│   │
│   ├── cbnu_crawler/         # 크롤링 시스템
│   │   ├── cbnu_crawler/     # Scrapy 프로젝트
│   │   │   ├── spiders/      # 정기 크롤러
│   │   │   │   ├── calendar_spider.py
│   │   │   │   ├── cbnu_notice_spider.py
│   │   │   │   └── dorm_final_spider.py
│   │   │   ├── pipelines.py  # 데이터 처리 파이프라인
│   │   │   └── settings.py   # Scrapy 설정
│   │   │
│   │   ├── spiders/          # 일회성 크롤러
│   │   │   └── software_spider.py
│   │   │
│   │   └── crawl_*.py        # 독립 크롤링 스크립트
│   │
│   ├── scripts/              # 데이터 처리 스크립트
│   │   ├── embed_software_data.py    # 임베딩 생성
│   │   ├── import_software_data.py   # 데이터 임포트
│   │   └── save_software_data.py     # 데이터 저장
│   │
│   ├── requirements.txt      # Python 패키지
│   ├── manage.py            # Django 관리 스크립트
│   └── .env                 # 환경 변수
│
├── frontend/                 # React 프론트엔드
│   ├── src/
│   │   ├── pages/           # 페이지 컴포넌트
│   │   ├── components/      # 재사용 컴포넌트
│   │   ├── App.js          # 메인 앱
│   │   └── index.js        # 진입점
│   │
│   ├── public/
│   ├── package.json
│   └── package-lock.json
│
└── scripts/                 # 시스템 관리 스크립트
    ├── start_all.sh        # 시스템 시작
    └── stop_all.sh         # 시스템 종료
```

---

## 🚀 설치 및 실행

### 1. 사전 요구사항
- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Chrome/Chromium (크롤링용)

### 2. 환경 설정

#### Backend 설정
```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 환경 변수 설정 (.env 파일)
DB_NAME=cbnu_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# 데이터베이스 마이그레이션
python manage.py migrate

# 관리자 계정 생성
python manage.py createsuperuser
```

#### Frontend 설정
```bash
cd frontend

# 패키지 설치
npm install
```

### 3. 시스템 실행

#### 간편 실행 (권장)
```bash
# 프로젝트 루트에서
./scripts/start_all.sh
```

#### 개별 실행
```bash
# Backend (터미널 1)
cd backend
source venv/bin/activate
python manage.py runserver 8000

# Frontend (터미널 2)
cd frontend
npm start
```

### 4. 접속
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/
- **Admin**: http://localhost:8000/admin/

### 5. 시스템 종료
```bash
./scripts/stop_all.sh
```

---

## 🛠️ 기술 스택

### Backend
- **Framework**: Django 5.0
- **Database**: PostgreSQL (pgvector 확장)
- **AI/ML**:
  - LangChain (RAG 파이프라인)
  - Sentence Transformers (임베딩)
  - Ollama (로컬 LLM)
- **Crawling**:
  - Scrapy (정기 크롤링)
  - Selenium (동적 페이지 크롤링)
- **API**: Django REST Framework

### Frontend
- **Framework**: React 18
- **Styling**: CSS3
- **HTTP Client**: Axios

### Infrastructure
- **Vector DB**: PostgreSQL + pgvector
- **Embedding Model**: jhgan/ko-sroberta-multitask
- **LLM**: Ollama (EEVE-Korean-10.8B)

---

## 📡 API 엔드포인트

### 채팅
- `POST /chat/message/` - 채팅 메시지 전송
  ```json
  {
    "message": "소프트웨어학부 공지사항 알려줘",
    "session_id": "user123",
    "user_id": "user123"
  }
  ```

### 일정 관리
- `GET /chat/events/` - 일정 목록 조회
- `POST /chat/events/add/` - 일정 추가
  ```json
  {
    "user_id": "user123",
    "title": "중간고사",
    "start_date": "2025-04-15",
    "end_date": "2025-04-19",
    "description": "중간고사 기간"
  }
  ```
- `DELETE /chat/events/<event_id>/` - 일정 삭제

### 구글 캘린더 연동
- `GET /chat/google/status/` - 연동 상태 확인
- `GET /chat/google/auth/` - OAuth 인증 시작
- `GET /chat/google/callback/` - OAuth 콜백
- `POST /chat/google/disconnect/` - 연동 해제
- `POST /chat/events/<event_id>/sync-to-google/` - 구글 캘린더 동기화

---

## 🔧 데이터 관리

### 크롤링 실행
```bash
cd backend

# 정기 크롤러 실행 (Scrapy)
python manage.py run_crawler

# 소프트웨어학부 크롤링
python cbnu_crawler/crawl_software_complete.py

# 졸업요건 크롤링
python cbnu_crawler/crawl_graduation.py
```

### RAG 인덱싱
```bash
# 전체 인덱스 생성
python manage.py run_rag_index

# 인덱스 업데이트
python manage.py run_rag_update
```

### 데이터 임포트
```bash
# 크롤링 결과 DB 저장 + 임베딩
python scripts/import_software_data.py

# DB 저장만
python scripts/save_software_data.py

# 임베딩만 생성
python scripts/embed_software_data.py
```

---

## 📊 데이터베이스 모델

### ChatMessage
- 채팅 메시지 저장
- 세션별 대화 기록 관리

### ChbNotice
- 충북대 공지사항 저장
- 게시판 타입별 분류 (학교, 학부, 기숙사)

### NoticeRagIndex
- 공지사항 벡터 임베딩 저장
- pgvector를 활용한 유사도 검색

### UserEvent
- 사용자 일정 저장
- 구글 캘린더 연동 정보

### GoogleCalendarToken
- OAuth 토큰 저장
- 구글 캘린더 API 인증

---

## 🔐 보안

- **환경 변수**: 민감 정보는 `.env` 파일로 관리
- **OAuth 2.0**: 구글 캘린더 안전한 인증
- **CSRF 보호**: Django CSRF 토큰 사용
- **SQL Injection 방지**: Django ORM 사용

---

## 📝 라이센스

이 프로젝트는 교육 목적으로 개발되었습니다.

---

## 👥 개발팀

충북대학교 소프트웨어학부 산학프로젝트 팀

---

## 📞 문의

프로젝트 관련 문의사항은 이슈를 등록해주세요.
