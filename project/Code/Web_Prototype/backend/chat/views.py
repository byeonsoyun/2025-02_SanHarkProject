import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# 기존 텍스트 챗 메시지 처리 예제
@csrf_exempt
def chat_message(request):
    if request.method == "POST":
        import json
        data = json.loads(request.body)
        message = data.get("message", "")
        # 여기서 실제 챗GPT 처리 로직 연결 가능
        reply = f"서버 응답: {message}"  # 임시 응답
        return JsonResponse({"reply": reply})
    return JsonResponse({"error": "POST 요청만 가능"}, status=400)


# PDF 업로드 처리
@csrf_exempt
def upload_pdf(request):
    if request.method == "POST" and request.FILES.get("pdf"):
        pdf_file = request.FILES["pdf"]
        save_dir = os.path.join(settings.MEDIA_ROOT, "uploaded_pdfs")
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, pdf_file.name)

        # 파일 저장
        with open(file_path, "wb+") as f:
            for chunk in pdf_file.chunks():
                f.write(chunk)

        # PDF 전송 성공 메시지 반환
        reply = f"[PDF 전송] {pdf_file.name}"
        return JsonResponse({"reply": reply})

    return JsonResponse({"error": "PDF 파일이 없습니다."}, status=400)
