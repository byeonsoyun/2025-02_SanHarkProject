#!/bin/bash

# 충북대 공지사항 챗봇 시스템 전체 실행 스크립트

echo "🚀 충북대 공지사항 챗봇 시스템 시작"
echo "======================================"

# 1. Ollama 실행 확인
echo ""
echo "1️⃣ Ollama 확인 중..."
if ! pgrep -x "ollama" > /dev/null; then
    echo "⚠️  Ollama가 실행되지 않았습니다."
    echo "   다음 명령어로 Ollama를 실행하세요:"
    echo "   ollama serve"
    echo ""
    read -p "Ollama를 백그라운드에서 실행하시겠습니까? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        nohup ollama serve > ~/SanHark_CBNU/ollama.log 2>&1 &
        echo "✅ Ollama 시작됨 (PID: $!)"
        sleep 3
    else
        echo "❌ Ollama 없이 계속할 수 없습니다. 종료합니다."
        exit 1
    fi
else
    echo "✅ Ollama 실행 중"
fi

# 2. PostgreSQL 확인
echo ""
echo "2️⃣ PostgreSQL 확인 중..."
if ! pg_isready -q; then
    echo "⚠️  PostgreSQL이 실행되지 않았습니다."
    echo "   다음 명령어로 PostgreSQL을 실행하세요:"
    echo "   brew services start postgresql@14"
    exit 1
else
    echo "✅ PostgreSQL 실행 중"
fi

# 3. 백엔드 실행
echo ""
echo "3️⃣ Django 백엔드 시작 중..."
cd ~/SanHark_CBNU/code/backend/cbnu_chatbot/backend
source venv/bin/activate
nohup python manage.py runserver > ~/SanHark_CBNU/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ 백엔드 시작됨 (PID: $BACKEND_PID)"

# 4. 프론트엔드 실행
echo ""
echo "4️⃣ React 프론트엔드 시작 중..."
cd ~/SanHark_CBNU/code/frontend
nohup npm start > ~/SanHark_CBNU/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ 프론트엔드 시작됨 (PID: $FRONTEND_PID)"

echo ""
echo "======================================"
echo "✨ 모든 서비스가 시작되었습니다!"
echo ""
echo "📍 접속 정보:"
echo "   - 프론트엔드: http://localhost:3000"
echo "   - 백엔드 API: http://localhost:8000"
echo "   - Ollama: http://localhost:11434"
echo ""
echo "📝 로그 파일:"
echo "   - Ollama: ~/SanHark_CBNU/ollama.log"
echo "   - 백엔드: ~/SanHark_CBNU/backend.log"
echo "   - 프론트엔드: ~/SanHark_CBNU/frontend.log"
echo ""
echo "🛑 종료 방법:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   또는 ~/SanHark_CBNU/stop_all.sh 실행"
echo ""
echo "PID 저장 중..."
echo "$BACKEND_PID" > ~/SanHark_CBNU/.backend.pid
echo "$FRONTEND_PID" > ~/SanHark_CBNU/.frontend.pid

echo "✅ 완료! 브라우저에서 http://localhost:3000 을 열어주세요."
