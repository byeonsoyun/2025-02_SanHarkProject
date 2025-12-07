#!/bin/bash

echo "🤖 충북대 공지사항 챗봇 모델 설정"
echo "===================================="

MODEL_NAME="cbnu-chatbot"

# 1. 기존 모델 확인
echo ""
echo "1️⃣ 기존 모델 확인 중..."
if ollama list | grep -q "$MODEL_NAME"; then
    echo "⚠️  기존 $MODEL_NAME 모델이 존재합니다."
    read -p "   삭제하고 새로 만드시겠습니까? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ollama rm $MODEL_NAME
        echo "✅ 기존 모델 삭제됨"
    else
        echo "❌ 취소되었습니다."
        exit 0
    fi
fi

# 2. 새 모델 생성
echo ""
echo "2️⃣ 새 모델 생성 중..."
cd ~/SanHark_CBNU
ollama create $MODEL_NAME -f Modelfile

if [ $? -eq 0 ]; then
    echo "✅ $MODEL_NAME 모델이 생성되었습니다!"
else
    echo "❌ 모델 생성 실패"
    exit 1
fi

# 3. 모델 테스트
echo ""
echo "3️⃣ 모델 테스트 중..."
echo "질문: 안녕하세요"
ollama run $MODEL_NAME "안녕하세요. 충북대 공지사항에 대해 물어보세요."

echo ""
echo "===================================="
echo "✅ 설정 완료!"
echo ""
echo "📝 Django 설정 업데이트:"
echo "   ~/SanHark_CBNU/code/backend/cbnu_chatbot/backend/.env 파일에서"
echo "   OLLAMA_MODEL=$MODEL_NAME"
echo ""
echo "🧪 모델 테스트:"
echo "   ollama run $MODEL_NAME"
echo ""
