from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from ..models import UserProfile, Skill, UserSkill, Experience, Education
from .serializers import (
    UserProfileSerializer, UserProfileCreateSerializer, SkillSerializer,
    UserSkillSerializer, ExperienceSerializer, EducationSerializer
)


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserProfileCreateSerializer
        return UserProfileSerializer
    
    @action(detail=True, methods=['post'])
    def complete_profile(self, request, pk=None):
        profile = self.get_object()
        profile.profile_completed = True
        profile.save()
        return Response({'message': 'Profile marked as completed'})
    
    @action(detail=True, methods=['post'])
    def complete_onboarding(self, request, pk=None):
        profile = self.get_object()
        profile.onboarding_completed = True
        profile.save()
        return Response({'message': 'Onboarding completed'})


class SkillViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    
    def get_queryset(self):
        queryset = Skill.objects.all()
        category = self.request.query_params.get('category', None)
        search = self.request.query_params.get('search', None)
        
        if category:
            queryset = queryset.filter(category=category)
        if search:
            queryset = queryset.filter(name__icontains=search)
            
        return queryset.order_by('-popularity_score', 'name')


class UserSkillListView(generics.ListCreateAPIView):
    serializer_class = UserSkillSerializer
    
    def get_queryset(self):
        profile_id = self.kwargs['profile_id']
        return UserSkill.objects.filter(user_profile_id=profile_id)
    
    def perform_create(self, serializer):
        profile_id = self.kwargs['profile_id']
        profile = get_object_or_404(UserProfile, id=profile_id)
        serializer.save(user_profile=profile)


class ExperienceListView(generics.ListCreateAPIView):
    serializer_class = ExperienceSerializer
    
    def get_queryset(self):
        profile_id = self.kwargs['profile_id']
        return Experience.objects.filter(user_profile_id=profile_id)
    
    def perform_create(self, serializer):
        profile_id = self.kwargs['profile_id']
        profile = get_object_or_404(UserProfile, id=profile_id)
        serializer.save(user_profile=profile)


class EducationListView(generics.ListCreateAPIView):
    serializer_class = EducationSerializer
    
    def get_queryset(self):
        profile_id = self.kwargs['profile_id']
        return Education.objects.filter(user_profile_id=profile_id)
    
    def perform_create(self, serializer):
        profile_id = self.kwargs['profile_id']
        profile = get_object_or_404(UserProfile, id=profile_id)
        serializer.save(user_profile=profile)