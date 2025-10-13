from django.http import HttpResponse

def home(request):
    return HttpResponse("홈페이지입니다.")
