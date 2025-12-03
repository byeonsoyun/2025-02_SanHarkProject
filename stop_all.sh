#!/bin/bash

echo "🛑 충북대 공지사항 챗봇 시스템 종료 중..."

# PID 파일에서 읽기
if [ -f ~/SanHark_CBNU/.backend.pid ]; then
    BACKEND_PID=$(cat ~/SanHark_CBNU/.backend.pid)
    if ps -p $BACKEND_PID > /dev/null; then
        kill $BACKEND_PID
        echo "✅ 백엔드 종료됨 (PID: $BACKEND_PID)"
    fi
    rm ~/SanHark_CBNU/.backend.pid
fi

if [ -f ~/SanHark_CBNU/.frontend.pid ]; then
    FRONTEND_PID=$(cat ~/SanHark_CBNU/.frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null; then
        kill $FRONTEND_PID
        echo "✅ 프론트엔드 종료됨 (PID: $FRONTEND_PID)"
    fi
    rm ~/SanHark_CBNU/.frontend.pid
fi

# React 개발 서버 프로세스 강제 종료
pkill -f "react-scripts start" 2>/dev/null && echo "✅ React 프로세스 종료됨"

echo "✅ 모든 서비스가 종료되었습니다."
