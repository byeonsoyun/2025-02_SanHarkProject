from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def home(request):
    """API 홈 엔드포인트"""
    return JsonResponse({
        "message": "CBNU Notice Chatbot API",
        "version": "1.0",
        "endpoints": {
            "chat": "/api/chat/",
            "admin": "/admin/"
        }
    })


@csrf_exempt
def health_check(request):
    """헬스 체크 엔드포인트"""
    return JsonResponse({"status": "healthy"})
