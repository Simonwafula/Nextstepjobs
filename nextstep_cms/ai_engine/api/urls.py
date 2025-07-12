from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'ai-configurations', views.AIConfigurationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('analyze-job/', views.AnalyzeJobView.as_view(), name='analyze-job'),
    path('anonymous-search/', views.AnonymousSearchView.as_view(), name='anonymous-search'),
    path('ai-feedback/', views.AIFeedbackView.as_view(), name='ai-feedback'),
    path('usage-analytics/', views.UsageAnalyticsView.as_view(), name='usage-analytics'),
]