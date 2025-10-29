from django.http import HttpResponse
from django.http import JsonResponse

def ping(request):
    return JsonResponse({"message": "pong"})



def home(request):
    return HttpResponse("홈페이지입니다.")
