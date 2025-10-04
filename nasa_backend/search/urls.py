from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.search),
    path('smart-search/', views.smart_search, name='smart_search'),  # NEW
    path('research/', views.research_search, name='research_search'),  # NEW
]
