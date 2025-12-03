#!/bin/bash

echo "=========================================="
echo "충북대 공지사항 챗봇 시스템 설정"
echo "=========================================="

# 1. PostgreSQL 데이터베이스 생성
echo ""
echo "1️⃣ PostgreSQL 데이터베이스 설정..."
psql -U postgres << EOF
-- 데이터베이스 생성
DROP DATABASE IF EXISTS cbnu_chatbot_db;
CREATE DATABASE cbnu_chatbot_db;

-- 사용자 생성
DROP USER IF EXISTS cbnu_user;
CREATE USER cbnu_user WITH PASSWORD '1111';

-- 권한 부여
GRANT ALL PRIVILEGES ON DATABASE cbnu_chatbot_db TO cbnu_user;

-- cbnu_chatbot_db에 연결
\c cbnu_chatbot_db

-- pgvector 확장 설치
CREATE EXTENSION IF NOT EXISTS vector;

-- 스키마 권한 부여
GRANT ALL ON SCHEMA public TO cbnu_user;

EOF

if [ $? -eq 0 ]; then
    echo "✅ 데이터베이스 설정 완료"
else
    echo "❌ 데이터베이스 설정 실패"
    exit 1
fi

# 2. Python 가상환경 생성
echo ""
echo "2️⃣ Python 가상환경 설정..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 가상환경 생성 완료"
else
    echo "⚠️ 가상환경이 이미 존재합니다"
fi

# 3. 패키지 설치
echo ""
echo "3️⃣ Python 패키지 설치..."
source venv/bin/activate
pip install --upgrade pip
pip install -r ../requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ 패키지 설치 완료"
else
    echo "❌ 패키지 설치 실패"
    exit 1
fi

# 4. Django 마이그레이션
echo ""
echo "4️⃣ Django 마이그레이션..."
python manage.py makemigrations
python manage.py migrate

if [ $? -eq 0 ]; then
    echo "✅ 마이그레이션 완료"
else
    echo "❌ 마이그레이션 실패"
    exit 1
fi

# 5. 완료 메시지
echo ""
echo "=========================================="
echo "✅ 설정 완료!"
echo "=========================================="
echo ""
echo "다음 단계:"
echo "1. 크롤러 실행: python manage.py run_crawler"
echo "2. RAG 인덱싱: python manage.py run_rag_index"
echo "3. 서버 실행: python manage.py runserver"
echo ""
echo "Ollama 확인: ollama list"
echo "모델 다운로드: ollama pull llama3"
echo ""
