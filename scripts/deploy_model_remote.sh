#!/bin/bash

# 외부 GPU 서버 정보 (수정 필요)
REMOTE_USER="your_username"
REMOTE_HOST="your_gpu_server_ip"
REMOTE_PORT="22"

echo "🚀 외부 GPU 서버에 모델 배포"
echo "===================================="

# 서버 정보 입력
read -p "GPU 서버 사용자명: " REMOTE_USER
read -p "GPU 서버 IP/호스트: " REMOTE_HOST
read -p "SSH 포트 (기본 22): " REMOTE_PORT
REMOTE_PORT=${REMOTE_PORT:-22}

echo ""
echo "📤 Modelfile 업로드 중..."
scp -P $REMOTE_PORT ~/SanHark_CBNU/Modelfile ${REMOTE_USER}@${REMOTE_HOST}:~/

if [ $? -ne 0 ]; then
    echo "❌ 업로드 실패"
    exit 1
fi

echo "✅ 업로드 완료"

echo ""
echo "🤖 원격 서버에서 모델 생성 중..."
ssh -p $REMOTE_PORT ${REMOTE_USER}@${REMOTE_HOST} << 'ENDSSH'
cd ~
ollama create cbnu-chatbot -f Modelfile
if [ $? -eq 0 ]; then
    echo "✅ cbnu-chatbot 모델 생성 완료"
    ollama list | grep cbnu-chatbot
else
    echo "❌ 모델 생성 실패"
    exit 1
fi
ENDSSH

echo ""
echo "===================================="
echo "✅ 배포 완료!"
echo ""
echo "📝 로컬 .env 파일 업데이트:"
echo "   LLM_API_URL=http://${REMOTE_HOST}:11434/api/generate"
echo "   LLM_MODEL_NAME=cbnu-chatbot"
echo ""
