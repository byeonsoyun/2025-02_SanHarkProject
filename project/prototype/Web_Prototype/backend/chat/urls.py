from django.urls import path
from . import views

urlpatterns = [
    path('', views.ping, name='chat_ping'),  # ping 뷰 연결
]
