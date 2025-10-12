from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.search_law, name='search_law'),
]
