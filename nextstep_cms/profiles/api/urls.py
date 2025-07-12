from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'profiles', views.UserProfileViewSet)
router.register(r'skills', views.SkillViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('profiles/<uuid:profile_id>/skills/', views.UserSkillListView.as_view(), name='user-skills'),
    path('profiles/<uuid:profile_id>/experiences/', views.ExperienceListView.as_view(), name='user-experiences'),
    path('profiles/<uuid:profile_id>/education/', views.EducationListView.as_view(), name='user-education'),
]