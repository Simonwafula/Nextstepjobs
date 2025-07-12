from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'career-paths', views.CareerPathViewSet)
router.register(r'career-goals', views.CareerGoalViewSet)
router.register(r'market-insights', views.MarketInsightViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('career-advice/', views.CareerAdviceView.as_view(), name='career-advice'),
    path('skill-gap-analysis/', views.SkillGapAnalysisView.as_view(), name='skill-gap-analysis'),
    path('career-recommendations/<uuid:user_id>/', views.CareerRecommendationView.as_view(), name='career-recommendations'),
    path('degree-programs/', views.DegreeProgramsView.as_view(), name='degree-programs'),
    path('degree-career-search/', views.DegreeCareerSearchView.as_view(), name='degree-career-search'),
    path('popular-topics/', views.PopularTopicsView.as_view(), name='popular-topics'),
]