from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
import asyncio
import os

from ..models import (
    CareerPath, CareerAdviceSession, CareerGoal, SkillGapAnalysis,
    MarketInsight, CareerRecommendation
)
from profiles.models import UserProfile
from .serializers import (
    CareerPathSerializer, CareerAdviceSessionSerializer, CareerGoalSerializer,
    SkillGapAnalysisSerializer, MarketInsightSerializer, CareerRecommendationSerializer,
    CareerAdviceRequestSerializer, SkillGapAnalysisRequestSerializer,
    DegreeCareerSearchSerializer
)
from emergentintegrations.llm.chat import LlmChat, UserMessage


class CareerPathViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CareerPath.objects.all()
    serializer_class = CareerPathSerializer
    
    def get_queryset(self):
        queryset = CareerPath.objects.all()
        industry = self.request.query_params.get('industry')
        level = self.request.query_params.get('level')
        search = self.request.query_params.get('search')
        
        if industry:
            queryset = queryset.filter(industry__icontains=industry)
        if level:
            queryset = queryset.filter(level=level)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
            
        return queryset.order_by('-demand_score', 'name')


class CareerGoalViewSet(viewsets.ModelViewSet):
    serializer_class = CareerGoalSerializer
    
    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        if user_id:
            return CareerGoal.objects.filter(user_profile_id=user_id)
        return CareerGoal.objects.none()
    
    def perform_create(self, serializer):
        user_id = self.request.data.get('user_id')
        if user_id:
            user_profile = get_object_or_404(UserProfile, id=user_id)
            serializer.save(user_profile=user_profile)


class MarketInsightViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MarketInsight.objects.filter(is_current=True)
    serializer_class = MarketInsightSerializer
    
    def get_queryset(self):
        queryset = MarketInsight.objects.filter(is_current=True)
        insight_type = self.request.query_params.get('type')
        category = self.request.query_params.get('category')
        
        if insight_type:
            queryset = queryset.filter(insight_type=insight_type)
        if category:
            queryset = queryset.filter(category__icontains=category)
            
        return queryset.order_by('-confidence_score', '-created_at')


class CareerAdviceView(APIView):
    """Get AI-powered career advice"""
    
    def post(self, request):
        serializer = CareerAdviceRequestSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            query = serializer.validated_data['query']
            session_type = serializer.validated_data['session_type']
            
            try:
                user_profile = UserProfile.objects.get(id=user_id)
                
                # Generate AI advice
                advice_response = self._generate_career_advice(user_profile, query, session_type)
                
                if advice_response:
                    # Save advice session
                    advice_session = CareerAdviceSession.objects.create(
                        user_profile=user_profile,
                        query=query,
                        session_type=session_type,
                        advice=advice_response['advice'],
                        recommendations=advice_response.get('recommendations', []),
                        action_items=advice_response.get('action_items', []),
                        resources=advice_response.get('resources', []),
                        follow_up_questions=advice_response.get('follow_up_questions', [])
                    )
                    
                    serializer = CareerAdviceSessionSerializer(advice_session)
                    return Response(serializer.data)
                else:
                    return Response(
                        {'error': 'Failed to generate career advice'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                    
            except UserProfile.DoesNotExist:
                return Response(
                    {'error': 'User profile not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _generate_career_advice(self, user_profile, query, session_type):
        """Generate AI-powered career advice"""
        try:
            system_message = f"""You are NextStep's expert career advisor with deep knowledge of various industries, job markets, and career paths. 

            Provide personalized, actionable career advice based on the user's profile and specific questions. Your advice should be:
            1. Practical and actionable
            2. Based on current job market trends for 2025
            3. Tailored to their education and experience level
            4. Encouraging yet realistic
            5. Include specific next steps they can take

            Session Type: {session_type}
            """
            
            user_message = f"""
            User Question: {query}
            
            User Profile Context:
            - Name: {user_profile.name}
            - Education: {user_profile.education_level} in {user_profile.field_of_study}
            - Skills: {', '.join([skill.skill.name for skill in user_profile.skills.all()])}
            - Experience: {user_profile.experience_years} years
            - Current Role: {user_profile.current_role}
            - Career Interests: {', '.join(user_profile.career_interests)}
            
            Please provide detailed career advice addressing their question. Also include specific action items, useful resources, and follow-up questions they might consider.
            """
            
            # Initialize AI chat
            chat = LlmChat(
                api_key=os.environ.get('OPENAI_API_KEY'),
                session_id=f"career_advice_{user_profile.id}_{timezone.now().timestamp()}",
                system_message=system_message
            ).with_model("openai", "gpt-4")
            
            # Send message
            message = UserMessage(text=user_message)
            response = asyncio.run(chat.send_message(message))
            
            return {
                'advice': response,
                'recommendations': [],  # Could be extracted from response
                'action_items': [],     # Could be extracted from response
                'resources': [],        # Could be extracted from response
                'follow_up_questions': []  # Could be extracted from response
            }
            
        except Exception as e:
            print(f"Error generating career advice: {e}")
            return None


class SkillGapAnalysisView(APIView):
    """Analyze skill gaps for target roles"""
    
    def post(self, request):
        serializer = SkillGapAnalysisRequestSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            target_roles = serializer.validated_data['target_roles']
            
            try:
                user_profile = UserProfile.objects.get(id=user_id)
                
                # Perform skill gap analysis
                analysis = self._perform_skill_gap_analysis(user_profile, target_roles)
                
                if analysis:
                    # Save analysis
                    skill_gap_analysis = SkillGapAnalysis.objects.create(
                        user_profile=user_profile,
                        target_roles=target_roles,
                        **analysis
                    )
                    
                    serializer = SkillGapAnalysisSerializer(skill_gap_analysis)
                    return Response(serializer.data)
                else:
                    return Response(
                        {'error': 'Failed to perform skill gap analysis'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                    
            except UserProfile.DoesNotExist:
                return Response(
                    {'error': 'User profile not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _perform_skill_gap_analysis(self, user_profile, target_roles):
        """Perform AI-powered skill gap analysis"""
        try:
            # Get user's current skills
            current_skills = [skill.skill.name for skill in user_profile.skills.all()]
            
            # This would involve:
            # 1. Analyzing job postings for target roles to extract required skills
            # 2. Comparing with user's current skills
            # 3. Generating recommendations
            
            # Simplified implementation
            return {
                'current_skills': current_skills,
                'required_skills': [],  # Would be populated from job analysis
                'missing_skills': [],   # Calculated difference
                'skill_recommendations': [],
                'overall_gap_percentage': 0.0,
                'critical_gaps': [],
                'strength_areas': current_skills,
                'learning_path': [],
                'estimated_learning_time': 0,
                'priority_skills': [],
                'recommended_courses': [],
                'recommended_certifications': [],
                'practice_projects': []
            }
            
        except Exception as e:
            print(f"Error performing skill gap analysis: {e}")
            return None


class CareerRecommendationView(APIView):
    """Get career recommendations for a user"""
    
    def get(self, request, user_id):
        try:
            user_profile = UserProfile.objects.get(id=user_id)
            recommendations = CareerRecommendation.objects.filter(
                user_profile=user_profile,
                is_active=True
            ).order_by('-priority_score', '-created_at')
            
            serializer = CareerRecommendationSerializer(recommendations, many=True)
            return Response({
                'recommendations': serializer.data,
                'user_id': str(user_id)
            })
            
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class DegreeProgramsView(APIView):
    """Get comprehensive mapping of degree programs to career opportunities"""
    
    def get(self, request):
        degree_mappings = {
            "stem_fields": {
                "Computer Science": {
                    "direct_careers": [
                        "Software Developer/Engineer",
                        "Data Scientist",
                        "AI/Machine Learning Engineer",
                        "Cybersecurity Specialist",
                        "DevOps Engineer",
                        "Product Manager (Technical)",
                        "Research Scientist"
                    ],
                    "alternative_paths": [
                        "Digital Marketing Specialist",
                        "Technical Writer",
                        "IT Consultant",
                        "Startup Founder",
                        "Technical Sales Engineer"
                    ],
                    "skills_gap": [
                        "Industry-specific domain knowledge",
                        "Soft skills and communication",
                        "Project management",
                        "Cloud platforms proficiency",
                        "Advanced system design"
                    ]
                },
                # Add more degree mappings...
            },
            "business_fields": {
                # Business field mappings...
            },
            "liberal_arts": {
                # Liberal arts mappings...
            }
        }
        
        return Response(degree_mappings)


class DegreeCareerSearchView(APIView):
    """AI-powered search specifically for connecting degrees to careers"""
    
    def post(self, request):
        serializer = DegreeCareerSearchSerializer(data=request.data)
        if serializer.is_valid():
            degree = serializer.validated_data['degree']
            career_interest = serializer.validated_data.get('career_interest', '')
            
            # Generate AI guidance
            guidance = self._generate_degree_career_guidance(degree, career_interest)
            
            return Response({
                'degree': degree,
                'career_interest': career_interest,
                'guidance': guidance,
                'generated_at': timezone.now().isoformat()
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _generate_degree_career_guidance(self, degree, career_interest):
        """Generate AI guidance for degree-to-career mapping"""
        try:
            system_message = """You are a specialized academic and career counselor. Help students understand the connection between their degree program and career opportunities. Provide:

            1. **Direct Career Paths**: Jobs directly related to the degree
            2. **Alternative Career Paths**: Unexpected but viable career options
            3. **Skills Development**: What skills to develop beyond coursework
            4. **Education Enhancement**: Additional certifications, minors, or courses to consider
            5. **Timeline**: Realistic timeline from graduation to career establishment
            6. **Success Stories**: Examples of graduates who succeeded in various paths
            7. **Action Steps**: Specific next steps the student can take now

            Make your response practical, encouraging, and actionable."""
            
            user_message = f"""
            Student's Degree Program: {degree}
            Career Interest/Area: {career_interest}
            
            Please provide comprehensive guidance on how this degree can lead to career success, including both traditional and non-traditional paths.
            """
            
            # Initialize AI chat
            chat = LlmChat(
                api_key=os.environ.get('OPENAI_API_KEY'),
                session_id=f"degree_search_{timezone.now().timestamp()}",
                system_message=system_message
            ).with_model("openai", "gpt-4")
            
            # Send message
            message = UserMessage(text=user_message)
            response = asyncio.run(chat.send_message(message))
            
            return response
            
        except Exception as e:
            print(f"Error generating degree career guidance: {e}")
            return "Career guidance temporarily unavailable"


class PopularTopicsView(APIView):
    """Get popular career topics and trending searches"""
    
    def get(self, request):
        topics = {
            "trending_careers": [
                "AI/ML Engineer 🤖",
                "Data Scientist 📊",
                "Cybersecurity Specialist 🔒",
                "Product Manager 📱",
                "UX/UI Designer 🎨",
                "Cloud Engineer ☁️",
                "DevOps Engineer 🚀",
                "Digital Marketing Specialist 📈",
                "Full-Stack Developer 💻",
                "Blockchain Developer 🔗"
            ],
            "popular_questions": [
                "How to break into AI without a technical background? 🤖",
                "What skills will be most valuable in 2025? 🚀",
                "How to transition careers at 30+? 🔄",
                "Remote work opportunities in emerging fields 🏠",
                "Highest paying entry-level jobs in tech 💰",
                "How to negotiate salary like a pro? 💼"
            ],
            "industry_insights": [
                "Artificial Intelligence & Machine Learning 🤖",
                "Green Technology & Sustainability 🌱",
                "Healthcare & Biotechnology 🏥",
                "Fintech & Cryptocurrency 💳",
                "EdTech & Online Learning 📚",
                "Space Technology & Aerospace 🚀"
            ]
        }
        
        return Response(topics)