from django.urls import path
from . import views

urlpatterns = [
    path('message/', views.chat_message, name='chat_message'),
    path('events/', views.get_events, name='get_events'),
    path('user-events/', views.add_event, name='add_event'),
    path('user-events/<int:event_id>/', views.delete_event, name='delete_event'),
    path('user-events/<int:event_id>/sync-google/', views.sync_to_google, name='sync_to_google'),
    path('google/status/', views.google_status, name='google_status'),
    path('google/auth/', views.google_auth, name='google_auth'),
    path('google/callback/', views.google_callback, name='google_callback'),
    path('google/disconnect/', views.google_disconnect, name='google_disconnect'),
]
