# 충북대학교 공지사항 챗봇 시스템

민사법 챗봇 시스템을 기반으로 충북대 공지사항에 특화된 RAG 챗봇 시스템입니다.

## 🎯 주요 기능

- **자동 크롤링**: Scrapy 기반 충북대 공지사항 자동 수집
- **지능형 검색**: pgvector 기반 의미론적 유사도 검색 (768차원)
- **복잡도 감지**: 단순 검색 vs LLM 분석 자동 구분
- **맥락 유지**: 이전 대화를 기억하는 연속적 상담
- **RAG 시스템**: 검색 증강 생성으로 정확한 답변 제공

## 🏗️ 시스템 구조

```
사용자 질문
    ↓
복잡도 감지 (단순 검색 / LLM 분석)
    ↓
질문 임베딩 (ko-sroberta-multitask)
    ↓
pgvector 유사도 검색 (PostgreSQL)
    ↓
[단순] 구조화된 요약 반환
[복잡] LLM 생성 (Ollama + 검색 컨텍스트)
    ↓
답변 반환
```

## 📋 요구사항

- Python 3.11+
- PostgreSQL 14+ (with pgvector extension)
- Ollama (llama3 모델)
- 8GB+ RAM

## 🚀 빠른 시작

### 1. 자동 설정 (권장)

```bash
cd ~/SanHark_CBNU/code/backend/cbnu_chatbot/extracted_ver2/backend
./setup.sh
```

### 2. 수동 설정

#### 2.1 PostgreSQL 설정

```bash
# PostgreSQL 접속
psql -U postgres

# 데이터베이스 생성
CREATE DATABASE cbnu_chatbot_db;
CREATE USER cbnu_user WITH PASSWORD '1111';
GRANT ALL PRIVILEGES ON DATABASE cbnu_chatbot_db TO cbnu_user;

# pgvector 확장 설치
\c cbnu_chatbot_db
CREATE EXTENSION vector;
GRANT ALL ON SCHEMA public TO cbnu_user;
```

#### 2.2 Python 환경 설정

```bash
# 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 패키지 설치
pip install -r ../requirements.txt

# 마이그레이션
python manage.py makemigrations
python manage.py migrate
```

#### 2.3 Ollama 설정

```bash
# Ollama 설치 확인
ollama --version

# llama3 모델 다운로드
ollama pull llama3

# Ollama 서버 실행 (별도 터미널)
ollama serve
```

### 3. 데이터 수집 및 인덱싱

```bash
# 1. 공지사항 크롤링
python manage.py run_crawler

# 2. RAG 벡터 인덱싱
python manage.py run_rag_index

# 3. 결과 확인
python manage.py shell
>>> from chat.models import ChbNotice, NoticeRagIndex
>>> ChbNotice.objects.count()  # 크롤링된 공지사항 수
>>> NoticeRagIndex.objects.count()  # 인덱싱된 청크 수
```

### 4. 서버 실행

```bash
# Django 서버 실행
python manage.py runserver

# API 테스트
curl -X POST http://localhost:8000/chat/message/ \
  -H "Content-Type: application/json" \
  -d '{"message": "기숙사 신청 방법 알려줘", "session_id": "test123"}'
```

## 📊 데이터 모델

### ChbNotice (원본 공지사항)
- `notice_id`: 공지사항 고유 ID
- `title`: 제목
- `content`: 본문
- `board_type`: 게시판 종류 (일반/학사/장학)
- `post_date`: 게시일
- `source_url`: 원본 URL
- `is_active`: 활성 상태

### NoticeRagIndex (벡터 검색용)
- `text_chunk`: 텍스트 청크
- `metadata`: 메타데이터 (JSON)
- `embedding`: 768차원 벡터

### ChatMessage (대화 기록)
- `session_id`: 세션 ID
- `user_id`: 사용자 ID
- `role`: user/assistant
- `content`: 메시지 내용
- `timestamp`: 시간

## 🔧 복잡도 감지 로직

### 단순 검색 (DB 검색만)
- 키워드: 찾아줘, 알려줘, 검색, 보여줘, 있어?, 뭐야
- 예시: "기숙사 공지 찾아줘", "장학금 있어?"

### LLM 분석 (RAG + LLM)
- 분석적: 가장, 비교, 분석, 왜, 어떻게
- 추론: 근거, 이유, 방법, 의미
- 맥락: 그럼, 그러면, 앞서
- 예시: "기숙사 신청 방법은 어떻게 되나요?", "졸업요건에 대해 설명해줘"

## 📝 API 엔드포인트

### POST /chat/message/
채팅 메시지 전송

**Request:**
```json
{
  "message": "기숙사 신청 방법 알려줘",
  "session_id": "user123",
  "user_id": "guest"
}
```

**Response:**
```json
{
  "reply": "기숙사 신청 방법은...",
  "needs_llm": false,
  "results_count": 3
}
```

### GET /chat/history/?session_id=user123
채팅 기록 조회

### POST /chat/clear/
채팅 기록 삭제

## 🛠️ 관리 명령어

```bash
# 크롤러 실행
python manage.py run_crawler

# RAG 인덱싱 (전체 재구축)
python manage.py run_rag_index

# RAG 업데이트 (증분 업데이트)
python manage.py run_rag_update

# 데이터베이스 초기화
python db_schema_reset.py
```

## 🔍 테스트 질문 예시

### 단순 검색
- "기숙사 공지 찾아줘"
- "장학금 관련 공지 알려줘"
- "취업 공고 있어?"

### 복잡한 질문
- "소프트웨어학과 25학번 졸업요건은 뭐야?"
- "기숙사 신청 방법에 대해 자세히 설명해줘"
- "올해 취업공고에 뭐뭐 있는지 알려줘"

## 🐛 트러블슈팅

### pgvector 오류
```bash
# PostgreSQL에서 확장 설치
psql -U postgres -d cbnu_chatbot_db
CREATE EXTENSION vector;
```

### Ollama 연결 실패
```bash
# Ollama 서버 상태 확인
curl http://localhost:11434/api/tags

# 모델 확인
ollama list

# 모델 다운로드
ollama pull llama3
```

### 임베딩 모델 다운로드 느림
```bash
# 수동 다운로드 (첫 실행 시)
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('jhgan/ko-sroberta-multitask')"
```

### 크롤러 실행 오류
```bash
# Scrapy 설정 확인
cd cbnu_crawler
scrapy list  # Spider 목록 확인
```

## 📁 프로젝트 구조

```
backend/
├── chat/                    # 채팅 앱
│   ├── models.py           # 데이터 모델
│   ├── views.py            # API 뷰
│   ├── services.py         # RAG 서비스
│   └── management/
│       └── commands/       # 관리 명령어
├── cbnu_crawler/           # 크롤러
│   └── cbnu_crawler/
│       └── spiders/        # Spider 정의
├── backend/                # Django 설정
│   └── settings.py
├── manage.py
├── setup.sh               # 자동 설정 스크립트
└── README.md
```

## 🔄 민사법 시스템과의 차이점

| 항목 | 민사법 챗봇 | 충북대 챗봇 |
|------|------------|------------|
| 데이터 소스 | 판례 (76K) | 공지사항 (크롤링) |
| 수집 방식 | 수동 | 자동 (Scrapy) |
| 도메인 | 법률 | 대학 공지 |
| 모델 | civil-law-expert | llama3 |
| 데이터베이스 | civil_law_db | cbnu_chatbot_db |

## 📞 문의

- 프로젝트: 2025년 2학기 산학프로젝트
- 팀: SanHark Team

---

⭐ 이 프로젝트가 도움이 되셨다면 Star를 눌러주세요!
