# 충북대학교 공지사항 챗봇 시스템

2025년 2학기 산학프로젝트 - 충북대 공지사항 AI 챗봇

## 📁 프로젝트 구조

```
SanHark_CBNU/
├── README.md                    # 이 파일
├── QUICKSTART.md               # 빠른 시작 가이드
├── MERGE_SUMMARY.md            # 시스템 머지 보고서
├── code/
│   ├── backend/
│   │   └── cbnu_chatbot/
│   │       ├── requirements.txt
│   │       └── backend/        # Django 백엔드 (메인)
│   │           ├── setup.sh
│   │           ├── test_system.py
│   │           ├── README.md
│   │           ├── manage.py
│   │           ├── chat/       # 채팅 앱
│   │           ├── cbnu_crawler/  # 크롤러
│   │           └── backend/    # Django 설정
│   └── frontend/               # React 프론트엔드 (예정)
└── document/                   # 프로젝트 문서

```

## 🚀 빠른 시작

```bash
# 1. 백엔드 디렉토리로 이동
cd ~/SanHark_CBNU/code/backend/cbnu_chatbot/backend

# 2. 자동 설정 실행
./setup.sh

# 3. 데이터 수집
source venv/bin/activate
python manage.py run_crawler
python manage.py run_rag_index

# 4. 서버 실행
python manage.py runserver
```

자세한 내용은 [QUICKSTART.md](QUICKSTART.md)를 참조하세요.

## 🎯 주요 기능

- **자동 크롤링**: Scrapy 기반 충북대 공지사항 수집
- **지능형 검색**: pgvector 기반 의미론적 검색
- **복잡도 감지**: 단순 검색 vs LLM 분석 자동 구분
- **RAG 시스템**: 검색 증강 생성으로 정확한 답변
- **맥락 유지**: 이전 대화 기억

## 📚 문서

- [빠른 시작 가이드](QUICKSTART.md)
- [상세 문서](code/backend/cbnu_chatbot/backend/README.md)
- [머지 보고서](MERGE_SUMMARY.md)

## 🔗 관련 프로젝트

- **SanHark_legal**: 민사법 챗봇 시스템 (원본)

---

⭐ 2025년 2학기 산학프로젝트 - SanHark Team
