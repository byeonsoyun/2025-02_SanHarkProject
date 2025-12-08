#!/bin/bash

echo "🛑 Stopping SanHark_CBNU System..."

# Backend 종료
echo "📦 Stopping Backend..."
pkill -f "python manage.py runserver 8000"

# Frontend 종료
echo "🎨 Stopping Frontend..."
pkill -f "react-scripts start"

echo "✅ System Stopped!"
