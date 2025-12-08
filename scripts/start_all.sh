#!/bin/bash

echo "🚀 Starting SanHark_CBNU System..."

# Backend 시작
echo "📦 Starting Backend (Port 8000)..."
cd ~/SanHark_CBNU/backend
source venv/bin/activate
nohup python manage.py runserver 8000 > ~/SanHark_CBNU/logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Frontend 시작
echo "🎨 Starting Frontend (Port 3000)..."
cd ~/SanHark_CBNU/frontend
nohup npm start > ~/SanHark_CBNU/logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

echo ""
echo "✅ System Started!"
echo "   Frontend: http://localhost:3000"
echo "   Calendar: http://localhost:3000/calendar"
echo "   Backend:  http://localhost:8000/api/"
echo ""
echo "📋 Logs:"
echo "   Backend:  tail -f ~/SanHark_CBNU/logs/backend.log"
echo "   Frontend: tail -f ~/SanHark_CBNU/logs/frontend.log"
