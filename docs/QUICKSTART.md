# 충북대 공지사항 챗봇 - 빠른 시작 가이드

## 🚀 5분 안에 시작하기

### 1단계: 시스템 설정 (자동)

```bash
cd ~/SanHark_CBNU/code/backend/cbnu_chatbot/extracted_ver2/backend
./setup.sh
```

이 스크립트가 자동으로:
- PostgreSQL 데이터베이스 생성 (cbnu_chatbot_db)
- pgvector 확장 설치
- Python 가상환경 생성
- 필요한 패키지 설치
- Django 마이그레이션 실행

### 2단계: Ollama 확인

```bash
# Ollama 설치 확인
ollama --version

# llama3 모델 다운로드 (없는 경우)
ollama pull llama3

# Ollama 서버 실행 (별도 터미널)
ollama serve
```

### 3단계: 데이터 수집

```bash
# 가상환경 활성화
source venv/bin/activate

# 공지사항 크롤링 (2-3분 소요)
python manage.py run_crawler

# RAG 벡터 인덱싱 (5-10분 소요)
python manage.py run_rag_index
```

### 4단계: 시스템 테스트

```bash
# 전체 시스템 테스트
python test_system.py
```

모든 테스트가 통과하면 ✅ 표시가 나타납니다.

### 5단계: 서버 실행

```bash
# Django 서버 실행
python manage.py runserver
```

서버가 http://localhost:8000 에서 실행됩니다.

## 🧪 API 테스트

### 터미널에서 테스트

```bash
# 단순 검색 테스트
curl -X POST http://localhost:8000/chat/message/ \
  -H "Content-Type: application/json" \
  -d '{"message": "기숙사 공지 찾아줘", "session_id": "test123"}'

# 복잡한 질문 테스트 (LLM 사용)
curl -X POST http://localhost:8000/chat/message/ \
  -H "Content-Type: application/json" \
  -d '{"message": "기숙사 신청 방법에 대해 설명해줘", "session_id": "test123"}'

# 채팅 기록 조회
curl http://localhost:8000/chat/history/?session_id=test123
```

### Python에서 테스트

```python
import requests

url = "http://localhost:8000/chat/message/"
data = {
    "message": "장학금 공지 알려줘",
    "session_id": "test123",
    "user_id": "guest"
}

response = requests.post(url, json=data)
print(response.json())
```

## 📝 테스트 질문 예시

### 단순 검색 (빠른 응답)
- "기숙사 공지 찾아줘"
- "장학금 관련 공지 알려줘"
- "취업 공고 있어?"
- "학사 일정 보여줘"

### 복잡한 질문 (LLM 분석)
- "소프트웨어학과 25학번 졸업요건은 뭐야?"
- "기숙사 신청 방법에 대해 자세히 설명해줘"
- "올해 취업공고에 뭐뭐 있는지 알려줘"
- "장학금 신청 자격 요건을 비교해줘"

## 🔧 문제 해결

### PostgreSQL 연결 오류
```bash
# PostgreSQL 서비스 확인
brew services list | grep postgresql

# PostgreSQL 재시작
brew services restart postgresql@17
```

### pgvector 오류
```bash
# pgvector 확장 수동 설치
psql -U postgres -d cbnu_chatbot_db
CREATE EXTENSION vector;
```

### Ollama 연결 실패
```bash
# Ollama 상태 확인
curl http://localhost:11434/api/tags

# Ollama 재시작
pkill ollama
ollama serve
```

### 크롤링 데이터 없음
```bash
# 크롤러 재실행
python manage.py run_crawler

# 데이터 확인
python manage.py shell
>>> from chat.models import ChbNotice
>>> ChbNotice.objects.count()
```

### RAG 인덱스 없음
```bash
# 인덱싱 재실행
python manage.py run_rag_index

# 인덱스 확인
python manage.py shell
>>> from chat.models import NoticeRagIndex
>>> NoticeRagIndex.objects.count()
```

## 📊 시스템 상태 확인

```bash
# Django shell에서 확인
python manage.py shell

# 데이터 확인
>>> from chat.models import ChbNotice, NoticeRagIndex, ChatMessage
>>> print(f"공지사항: {ChbNotice.objects.count()}건")
>>> print(f"RAG 인덱스: {NoticeRagIndex.objects.count()}건")
>>> print(f"채팅 기록: {ChatMessage.objects.count()}건")

# 최근 공지사항 확인
>>> for notice in ChbNotice.objects.all()[:3]:
...     print(f"[{notice.board_type}] {notice.title}")

# RAG 서비스 테스트
>>> from chat.services import RAGService
>>> rag = RAGService()
>>> results = rag.retrieve_context("기숙사")
>>> print(f"검색 결과: {len(results)}건")
```

## 🎯 다음 단계

1. **프론트엔드 연동**: React 프론트엔드 설정
2. **크롤러 확장**: 학사공지, 장학공지 추가
3. **데이터 보강**: 졸업요건 등 구조화된 데이터 추가
4. **성능 최적화**: 캐싱, 인덱스 튜닝

## 📞 도움이 필요하신가요?

- 상세 문서: `backend/README.md`
- 시스템 테스트: `python test_system.py`
- 로그 확인: `backend/chat/logs/`

---

✨ 설정이 완료되었습니다! 이제 충북대 공지사항 챗봇을 사용할 수 있습니다.
