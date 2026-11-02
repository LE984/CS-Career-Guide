from django.urls import path
from .auth_urls import urlpatterns as auth_patterns
from ai_integration.senior_advice_views import senior_advice_list

urlpatterns = [*auth_patterns, path('api/ai/senior-advice/', senior_advice_list)]
