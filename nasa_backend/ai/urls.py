from django.urls import path
from .views import query_ai

urlpatterns = [
    path("query-ai/", query_ai),
]
