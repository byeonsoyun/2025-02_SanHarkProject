# 민사법 AI 챗봇 시스템 🏛️⚖️

대한민국 민사법 전문 AI 챗봇 시스템입니다. 76,291개의 실제 민사법 판례를 기반으로 법률 상담을 제공합니다.

## 🌟 주요 기능

- **📚 대규모 판례 데이터**: 76,291개 민사법 판례 (계약법, 불법행위법, 물권법, 손해배상, 민사소송)
- **🧠 지능형 질문 분류**: 단순 검색 vs 복잡한 AI 분석 자동 구분
- **💬 맥락 유지 대화**: 이전 대화 내용을 기억하는 연속적 상담
- **🎨 현대적 UI**: 다크/라이트 테마, 멀티 채팅 관리
- **⚡ 하이브리드 처리**: 로컬 DB 검색 + 외부 GPU 서버 AI 분석

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React UI      │    │   Django API     │    │  External GPU   │
│   (Frontend)    │◄──►│   (Backend)      │◄──►│   (AI Model)    │
│                 │    │                  │    │                 │
│ • 채팅 인터페이스  │    │ • 76K 판례 DB     │    │ • civil-law-expert │
│ • 테마 지원       │    │ • 복잡도 감지      │    │ • 법률 전문 분석    │
│ • 멀티 세션       │    │ • 맥락 관리        │    │ • GPU 가속        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 빠른 시작

### 1. 저장소 클론
```bash
git clone https://github.com/yourusername/civil-law-chatbot.git
cd civil-law-chatbot
```

### 2. 백엔드 설정
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py runserver
```

### 3. 프론트엔드 설정
```bash
cd frontend
npm install
npm start
```

### 4. 브라우저에서 접속
http://localhost:3000

## 📋 시스템 요구사항

### 로컬 환경
- **Python**: 3.11+
- **Node.js**: 16+
- **메모리**: 8GB+ (권장 16GB)
- **저장공간**: 5GB+

### 외부 GPU 서버 (선택사항)
- **GPU**: NVIDIA 8GB+ VRAM
- **CUDA**: 12.1+
- **Ollama**: 최신 버전

## 🎯 사용 예시

### 단순 검색 (빠른 DB 검색)
```
"임대차 계약"
"손해배상"
"교통사고"
```

### 복잡한 분석 (AI 모델 활용)
```
"계약 위반 시 손해배상 범위는 어떻게 결정되나요?"
"임대차보증금 반환청구권과 우선변제권의 관계를 분석해주세요"
"부동산 매매계약 해제 시 중개수수료 반환 기준을 설명해주세요"
```

### 맥락 유지 대화
```
사용자: "교통사고 손해배상은 어떻게 계산하나요?"
AI: [상세한 교통사고 손해배상 설명]

사용자: "그럼 과실비율은 어떻게 정해지나요?"
AI: [앞선 교통사고 맥락을 고려한 과실비율 설명]
```

## ⚙️ 설정 관리

### GPU 서버 연결
```bash
# 외부 GPU 서버 사용
python3 switch_ollama.py external

# 로컬 모델 사용
python3 switch_ollama.py local

# 현재 설정 확인
python3 switch_ollama.py status
```

## 🔧 기술 스택

### Backend
- **Django**: 웹 프레임워크
- **SQLite**: 판례 데이터베이스
- **Python**: 백엔드 로직

### Frontend
- **React**: UI 프레임워크
- **Bootstrap**: 스타일링
- **Axios**: API 통신

### AI/ML
- **Ollama**: LLM 서버
- **Custom Models**: 민사법 전문 모델
- **FAISS**: 벡터 검색 (선택사항)

## 📊 데이터

- **총 판례 수**: 76,291개
- **분야**: 민사법 전문
  - 계약법 (매매, 임대차, 도급 등)
  - 불법행위법 (교통사고, 의료사고 등)
  - 물권법 (소유권, 담보물권 등)
  - 손해배상 (재산적/정신적 피해)
  - 민사소송 (절차, 증거, 판결 등)

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## ⚠️ 면책 조항

이 시스템은 교육 및 연구 목적으로 개발되었습니다. 실제 법률 문제에 대해서는 반드시 전문 변호사와 상담하시기 바랍니다.

## 📞 문의

- **개발팀**: SanHark Team
- **이메일**: contact@sanhark.com
- **프로젝트 링크**: https://github.com/yourusername/civil-law-chatbot

---

⭐ 이 프로젝트가 도움이 되셨다면 Star를 눌러주세요!
