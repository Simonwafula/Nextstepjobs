from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'jobs', views.JobPostingViewSet)
router.register(r'companies', views.CompanyViewSet)
router.register(r'saved-jobs', views.SavedJobViewSet)
router.register(r'job-alerts', views.JobAlertViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('jobs/search/', views.JobSearchView.as_view(), name='job-search'),
    path('jobs/scrape/', views.ScrapeJobsView.as_view(), name='scrape-jobs'),
    path('jobs/<uuid:job_id>/recommendations/<uuid:user_id>/', views.JobRecommendationsView.as_view(), name='job-recommendations'),
    path('jobs/<uuid:job_id>/match/<uuid:user_id>/', views.JobMatchView.as_view(), name='job-match'),
    path('market/analysis/', views.MarketAnalysisView.as_view(), name='market-analysis'),
]