# 충북대 공지사항 챗봇 시스템 시작 가이드

## 📋 시스템 구성

- **프론트엔드**: React (localhost:3000)
- **백엔드**: Django (localhost:8000)
- **데이터베이스**: PostgreSQL (localhost:5432)
- **LLM**: Ollama on GPU Server (10.198.138.249:22434)
- **데이터**: 1,950건 크롤링 완료, 1,949건 인덱싱 완료

---

## 🚀 시스템 시작 순서

### 1단계: GPU 서버 Ollama 실행

**터미널 1 - GPU 서버 접속:**
```bash
ssh sh001@10.198.138.249 -p 11122
```

**Ollama 실행 (GPU 서버에서):**
```bash
# 기존 Ollama 프로세스 확인
ps aux | grep ollama

# 실행 중이 아니면 시작
OLLAMA_HOST=0.0.0.0:11434 nohup ollama serve > ~/ollama.log 2>&1 &

# 확인
curl http://localhost:11434/api/tags
```

**모델 확인:**
```bash
ollama list
# cbnu1:latest 모델이 있어야 함
```

---

### 2단계: PostgreSQL 실행

**터미널 2 - 로컬:**
```bash
# PostgreSQL 상태 확인
pg_isready

# 실행 중이 아니면 시작
brew services start postgresql@14
```

---

### 3단계: Django 백엔드 실행

**터미널 3 - 로컬:**
```bash
cd ~/SanHark_CBNU/code/backend/cbnu_chatbot/backend
source venv/bin/activate
python manage.py runserver
```

**확인:**
- http://localhost:8000/admin 접속 가능
- 콘솔에 에러 없음

---

### 4단계: React 프론트엔드 실행

**터미널 4 - 로컬:**
```bash
cd ~/SanHark_CBNU/code/frontend
npm start
```

**자동으로 브라우저가 열림:**
- http://localhost:3000

---

## 🧪 시스템 테스트

### 1. 백엔드 API 테스트
```bash
curl -X POST http://localhost:8000/api/message/ \
  -H "Content-Type: application/json" \
  -d '{"message":"장학금 공지 알려줘"}'
```

### 2. 프론트엔드 테스트
1. http://localhost:3000 접속
2. Chatbot 페이지로 이동
3. 질문 입력: "최근 공지사항 알려줘"
4. 응답 확인

---

## 🛑 시스템 종료

### 자동 종료 (권장)
```bash
~/SanHark_CBNU/stop_all.sh
```

### 수동 종료
```bash
# 프론트엔드: Ctrl+C (터미널 4)
# 백엔드: Ctrl+C (터미널 3)
# PostgreSQL: brew services stop postgresql@14
# GPU 서버 Ollama: ssh로 접속 후 pkill ollama
```

---

## 📝 주요 설정 파일

### 백엔드 설정
**파일**: `~/SanHark_CBNU/code/backend/cbnu_chatbot/backend/backend/settings.py`
```python
LLM_API_URL = "http://10.198.138.249:22434/api/generate"
LLM_MODEL_NAME = "cbnu1"
```

### 프론트엔드 API 엔드포인트
**파일**: `~/SanHark_CBNU/code/frontend/src/pages/Chatbot.js`
```javascript
http://localhost:8000/api/message/
http://localhost:8000/api/clear/
```

---

## 🔧 문제 해결

### 1. "LLM 서버 호출 중 오류"
```bash
# GPU 서버에서 Ollama 재시작
ssh sh001@10.198.138.249 -p 11122
pkill ollama
OLLAMA_HOST=0.0.0.0:11434 nohup ollama serve > ~/ollama.log 2>&1 &
```

### 2. "백엔드 서버 연결 불가"
```bash
# 백엔드 재시작
cd ~/SanHark_CBNU/code/backend/cbnu_chatbot/backend
source venv/bin/activate
python manage.py runserver
```

### 3. PostgreSQL 연결 오류
```bash
# PostgreSQL 재시작
brew services restart postgresql@14

# 데이터베이스 확인
psql -U cbnu_user -d cbnu_chatbot_db
```

### 4. 프론트엔드 빌드 오류
```bash
cd ~/SanHark_CBNU/code/frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

---

## 📊 데이터 관리

### 크롤링 재실행
```bash
cd ~/SanHark_CBNU/code/backend/cbnu_chatbot/backend
source venv/bin/activate

# 백그라운드 실행
nohup bash -c "cd cbnu_crawler && scrapy crawl cbnu_notice" > crawler.log 2>&1 &
```

### 인덱싱 재실행
```bash
cd ~/SanHark_CBNU/code/backend/cbnu_chatbot/backend
source venv/bin/activate
python manage.py run_rag_index
```

### 데이터 확인
```bash
cd ~/SanHark_CBNU/code/backend/cbnu_chatbot/backend
source venv/bin/activate
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()
from chat.models import ChbNotice, NoticeRagIndex
print(f'공지사항: {ChbNotice.objects.count()}건')
print(f'인덱스: {NoticeRagIndex.objects.count()}건')
"
```

---

## 🌐 접속 정보

| 서비스 | URL | 비고 |
|--------|-----|------|
| 프론트엔드 | http://localhost:3000 | React 개발 서버 |
| 백엔드 API | http://localhost:8000 | Django REST API |
| 관리자 페이지 | http://localhost:8000/admin | Django Admin |
| GPU Ollama | 10.198.138.249:22434 | 외부 GPU 서버 |
| PostgreSQL | localhost:5432 | 로컬 DB |

---

## 📁 주요 디렉토리 구조

```
~/SanHark_CBNU/
├── Modelfile                    # Ollama 모델 정의
├── STARTUP_GUIDE.md            # 이 파일
├── start_all.sh                # 자동 시작 스크립트
├── stop_all.sh                 # 자동 종료 스크립트
├── setup_model.sh              # 모델 생성 스크립트
├── code/
│   ├── backend/
│   │   └── cbnu_chatbot/
│   │       └── backend/
│   │           ├── manage.py
│   │           ├── backend/settings.py
│   │           ├── chat/          # 챗봇 앱
│   │           └── cbnu_crawler/  # 크롤러
│   └── frontend/
│       ├── src/
│       │   └── pages/Chatbot.js
│       └── package.json
└── document/                    # 프로젝트 문서
```

---

## ✅ 시작 체크리스트

- [ ] GPU 서버 Ollama 실행 확인
- [ ] PostgreSQL 실행 확인
- [ ] Django 백엔드 실행 (포트 8000)
- [ ] React 프론트엔드 실행 (포트 3000)
- [ ] 브라우저에서 http://localhost:3000 접속
- [ ] 챗봇 페이지에서 질문 테스트

---

**마지막 업데이트**: 2025-12-03
