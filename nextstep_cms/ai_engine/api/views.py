from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models
import asyncio
import os
import json

from ..models import (
    AIJobAnalysis, AnonymousSearch, AIConfiguration, 
    AIUsageAnalytics, AIFeedback
)
from profiles.models import UserProfile
from .serializers import (
    AIJobAnalysisSerializer, AnonymousSearchSerializer, AIConfigurationSerializer,
    AIFeedbackSerializer, JobAnalysisRequestSerializer, AnonymousSearchRequestSerializer
)
from emergentintegrations.llm.chat import LlmChat
from emergentintegrations.llm import UserMessage


class AIConfigurationViewSet(viewsets.ModelViewSet):
    queryset = AIConfiguration.objects.all()
    serializer_class = AIConfigurationSerializer
    
    def get_queryset(self):
        queryset = AIConfiguration.objects.all()
        config_type = self.request.query_params.get('type')
        is_active = self.request.query_params.get('active')
        
        if config_type:
            queryset = queryset.filter(config_type=config_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset.order_by('-is_active', 'config_type', 'name')


class AnalyzeJobView(APIView):
    """AI-powered job analysis for users"""
    
    def post(self, request):
        serializer = JobAnalysisRequestSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            job_description = serializer.validated_data['job_description']
            job_title = serializer.validated_data.get('job_title', '')
            company_name = serializer.validated_data.get('company_name', '')
            
            try:
                user_profile = UserProfile.objects.get(id=user_id)
                
                # Perform AI job analysis
                analysis_result = self._perform_job_analysis(
                    user_profile, job_description, job_title, company_name
                )
                
                if analysis_result:
                    # Save analysis
                    job_analysis = AIJobAnalysis.objects.create(
                        user_profile=user_profile,
                        job_description=job_description,
                        job_title=job_title,
                        company_name=company_name,
                        **analysis_result
                    )
                    
                    serializer = AIJobAnalysisSerializer(job_analysis)
                    return Response(serializer.data)
                else:
                    return Response(
                        {'error': 'Failed to analyze job description'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                    
            except UserProfile.DoesNotExist:
                return Response(
                    {'error': 'User profile not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _perform_job_analysis(self, user_profile, job_description, job_title, company_name):
        """Perform AI-powered job analysis"""
        try:
            system_message = """You are an expert career advisor and job market analyst. Analyze job descriptions and provide detailed insights about requirements, match assessment, and recommendations.

            Respond in JSON format with the following structure:
            {
                "analysis_summary": "Brief overview of the job and its key characteristics",
                "detailed_analysis": {
                    "role_overview": "What this role entails",
                    "key_requirements": "Main requirements and qualifications",
                    "company_culture": "Company culture indicators from the job posting"
                },
                "required_qualifications": {
                    "education": "Education requirements",
                    "experience": "Experience requirements",
                    "certifications": ["cert1", "cert2"]
                },
                "required_skills": ["skill1", "skill2"],
                "preferred_skills": ["skill1", "skill2"],
                "responsibilities": ["responsibility1", "responsibility2"],
                "career_level": "Entry/Junior/Mid/Senior level",
                "industry": "Industry category",
                "growth_potential": "Career growth potential",
                "work_environment": "Work environment description",
                "salary_analysis": {
                    "range": "Salary range if mentioned",
                    "market_comparison": "How it compares to market rates"
                },
                "culture_indicators": ["indicator1", "indicator2"],
                "company_values": ["value1", "value2"],
                "match_score": 0.85,
                "match_breakdown": {
                    "skills_match": 0.8,
                    "experience_match": 0.9,
                    "education_match": 0.85
                },
                "strengths": ["User's strengths for this role"],
                "gaps": ["Areas where user needs improvement"],
                "recommendations": ["Specific recommendations for the user"],
                "improvement_suggestions": ["How to improve candidacy for this role"]
            }"""
            
            user_message = f"""
            Analyze this job posting for the user:
            
            Job Title: {job_title}
            Company: {company_name}
            
            Job Description:
            {job_description}
            
            User Profile:
            - Name: {user_profile.name}
            - Education: {user_profile.education_level} in {user_profile.field_of_study}
            - Skills: {', '.join([skill.skill.name for skill in user_profile.skills.all()])}
            - Experience: {user_profile.experience_years} years
            - Current Role: {user_profile.current_role}
            - Career Interests: {', '.join(user_profile.career_interests)}
            
            Please provide a comprehensive analysis of this job and how well it matches the user's profile.
            """
            
            # Initialize AI chat
            chat = LlmChat(
                api_key=os.environ.get('OPENAI_API_KEY'),
                session_id=f"job_analysis_{user_profile.id}_{timezone.now().timestamp()}",
                system_message=system_message
            ).with_model("openai", "gpt-4")
            
            # Send message
            message = UserMessage(text=user_message)
            response = asyncio.run(chat.send_message(message))
            
            # Parse JSON response
            try:
                analysis = json.loads(response)
                return analysis
            except json.JSONDecodeError:
                # If not valid JSON, create basic structure
                return {
                    'analysis_summary': response[:500] + "..." if len(response) > 500 else response,
                    'detailed_analysis': {'role_overview': 'Analysis available in summary'},
                    'required_qualifications': {},
                    'required_skills': [],
                    'preferred_skills': [],
                    'responsibilities': [],
                    'match_score': 0.5,
                    'match_breakdown': {},
                    'strengths': [],
                    'gaps': [],
                    'recommendations': [],
                    'improvement_suggestions': []
                }
                
        except Exception as e:
            print(f"Error performing job analysis: {e}")
            return None


class AnonymousSearchView(APIView):
    """Anonymous career search without user registration"""
    
    def post(self, request):
        serializer = AnonymousSearchRequestSerializer(data=request.data)
        if serializer.is_valid():
            query = serializer.validated_data['query']
            search_type = serializer.validated_data['search_type']
            user_context = serializer.validated_data.get('user_context', {})
            
            # Generate AI response
            ai_response = self._generate_anonymous_search_response(query, search_type)
            
            if ai_response:
                # Save search
                anonymous_search = AnonymousSearch.objects.create(
                    query=query,
                    search_type=search_type,
                    response=ai_response['response'],
                    suggestions=ai_response.get('suggestions', []),
                    user_context=user_context,
                    session_id=request.session.session_key,
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    ip_address=self._get_client_ip(request),
                    referrer=request.META.get('HTTP_REFERER', '')
                )
                
                serializer = AnonymousSearchSerializer(anonymous_search)
                return Response(serializer.data)
            else:
                return Response(
                    {'error': 'Failed to generate career guidance'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _generate_anonymous_search_response(self, query, search_type):
        """Generate AI response for anonymous search"""
        try:
            system_messages = {
                'general': """You are NextStep's AI career advisor - an expert, friendly, and motivational career guidance specialist. Answer career-related questions with:
                1. Clear, practical advice with actionable steps
                2. Current industry insights and trends for 2025
                3. Specific next steps they can take immediately
                4. Educational requirements and skill development paths
                5. Growth opportunities and career progression
                6. Inspiring and motivational tone""",
                
                'career_path': """You are NextStep's career pathway specialist. Help users discover and navigate their ideal career journey by providing:
                1. Multiple career options in their area of interest
                2. Educational requirements and alternative pathways
                3. Typical career progression and timeline expectations
                4. Skills needed at each level with development strategies
                5. Salary expectations and earning potential
                6. Industry outlook and future opportunities""",
                
                'skills': """You are NextStep's skills development guru. Focus on empowering users with:
                1. Current in-demand skills in the relevant field for 2025
                2. How to develop these skills (courses, certifications, practice)
                3. Skill progression pathways with clear milestones
                4. Time investment needed and realistic expectations
                5. Best resources for learning (free and paid options)
                6. How skills translate to job opportunities""",
                
                'industry': """You are NextStep's industry intelligence specialist. Provide comprehensive insights about:
                1. Industry trends, growth patterns, and future outlook
                2. Major companies, employers, and emerging players
                3. Geographic job markets and remote opportunities
                4. Salary ranges, compensation packages, and benefits
                5. Entry points into the industry and career ladders
                6. Industry challenges and how to navigate them"""
            }
            
            system_message = system_messages.get(search_type, system_messages['general'])
            
            user_message = f"""
            User Query: {query}
            
            As NextStep's AI career advisor, provide comprehensive and inspiring career guidance addressing this question. Make it motivational, practical, and forward-looking for 2025 and beyond.
            """
            
            # Initialize AI chat
            chat = LlmChat(
                api_key=os.environ.get('OPENAI_API_KEY'),
                session_id=f"anonymous_search_{timezone.now().timestamp()}",
                system_message=system_message
            ).with_model("openai", "gpt-4")
            
            # Send message
            message = UserMessage(text=user_message)
            response = asyncio.run(chat.send_message(message))
            
            # Generate suggestions
            suggestions = [
                "What skills are most in-demand in this field for 2025?",
                "What are the fastest-growing career paths in this area?",
                "What education or certifications can accelerate my progress?",
                "What's the salary potential and growth outlook?"
            ]
            
            return {
                'response': response,
                'suggestions': suggestions
            }
            
        except Exception as e:
            print(f"Error generating anonymous search response: {e}")
            return None
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AIFeedbackView(APIView):
    """Submit feedback for AI-generated content"""
    
    def post(self, request):
        serializer = AIFeedbackSerializer(data=request.data)
        if serializer.is_valid():
            user_id = request.data.get('user_id')
            
            if user_id:
                try:
                    user_profile = UserProfile.objects.get(id=user_id)
                    serializer.save(user_profile=user_profile)
                except UserProfile.DoesNotExist:
                    serializer.save(user_profile=None)
            else:
                serializer.save(user_profile=None)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsageAnalyticsView(APIView):
    """Get AI usage analytics"""
    
    def get(self, request):
        # Get query parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        feature_type = request.query_params.get('feature_type')
        
        # Build query
        queryset = AIUsageAnalytics.objects.all()
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        if feature_type:
            queryset = queryset.filter(feature_type=feature_type)
        
        # Calculate statistics
        total_requests = queryset.count()
        avg_processing_time = queryset.aggregate(
            avg_time=models.Avg('processing_time')
        )['avg_time'] or 0
        
        # Feature usage breakdown
        feature_usage = queryset.values('feature_type').annotate(
            count=models.Count('id')
        ).order_by('-count')
        
        return Response({
            'total_requests': total_requests,
            'average_processing_time': round(avg_processing_time, 3),
            'feature_usage': list(feature_usage),
            'period': {
                'start_date': start_date,
                'end_date': end_date
            }
        })