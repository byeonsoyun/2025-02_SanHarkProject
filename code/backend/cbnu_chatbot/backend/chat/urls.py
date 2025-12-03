from django.urls import path
from . import views

urlpatterns = [
    path('message/', views.chat_message, name='chat_message'),
    path('history/', views.get_chat_history, name='get_chat_history'),
    path('clear/', views.clear_chat_history, name='clear_chat_history'),
    path('calendar/events/', views.get_calendar_events, name='get_calendar_events'),
    path('calendar/extract/', views.extract_event_from_notice, name='extract_event'),
]
