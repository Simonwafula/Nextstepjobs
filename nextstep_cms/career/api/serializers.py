from rest_framework import serializers
from ..models import (
    CareerPath, CareerAdviceSession, CareerGoal, SkillGapAnalysis,
    MarketInsight, CareerRecommendation
)


class CareerPathSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerPath
        fields = [
            'id', 'name', 'slug', 'description', 'industry', 'field', 'level',
            'typical_education', 'required_skills', 'preferred_skills', 'typical_experience',
            'average_salary_min', 'average_salary_max', 'growth_outlook',
            'previous_roles', 'next_roles', 'alternative_paths',
            'demand_score', 'competition_score', 'satisfaction_score'
        ]


class CareerAdviceSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerAdviceSession
        fields = [
            'id', 'query', 'session_type', 'advice', 'recommendations',
            'action_items', 'resources', 'follow_up_questions',
            'rating', 'feedback', 'was_helpful', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'advice', 'recommendations', 'action_items']


class CareerGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerGoal
        fields = [
            'id', 'title', 'description', 'category', 'target_date',
            'is_completed', 'completion_date', 'progress_percentage',
            'milestones', 'completed_milestones', 'priority', 'difficulty',
            'action_plan', 'resources_needed', 'barriers', 'notes',
            'last_reviewed', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SkillGapAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillGapAnalysis
        fields = [
            'id', 'target_roles', 'current_skills', 'required_skills',
            'missing_skills', 'skill_recommendations', 'overall_gap_percentage',
            'critical_gaps', 'strength_areas', 'learning_path',
            'estimated_learning_time', 'priority_skills', 'recommended_courses',
            'recommended_certifications', 'practice_projects', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class MarketInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketInsight
        fields = [
            'id', 'insight_type', 'category', 'title', 'summary',
            'detailed_analysis', 'demand_trend', 'salary_trend',
            'key_statistics', 'trending_skills', 'top_companies',
            'geographic_hotspots', 'future_outlook', 'predicted_changes',
            'opportunities', 'challenges', 'confidence_score',
            'valid_from', 'valid_until', 'is_current'
        ]


class CareerRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerRecommendation
        fields = [
            'id', 'recommendation_type', 'title', 'description',
            'detailed_advice', 'action_items', 'resources', 'timeline',
            'confidence_score', 'priority_score', 'viewed', 'rating',
            'feedback', 'implemented', 'is_active', 'expires_at'
        ]


class CareerAdviceRequestSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    query = serializers.CharField(max_length=2000)
    session_type = serializers.ChoiceField(
        choices=[
            ('general', 'General Career Advice'),
            ('career_change', 'Career Change'),
            ('skill_development', 'Skill Development'),
            ('salary_negotiation', 'Salary Negotiation'),
            ('interview_prep', 'Interview Preparation'),
            ('resume_review', 'Resume Review'),
            ('industry_insights', 'Industry Insights'),
        ],
        default='general'
    )


class SkillGapAnalysisRequestSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    target_roles = serializers.ListField(child=serializers.CharField())


class DegreeCareerSearchSerializer(serializers.Serializer):
    degree = serializers.CharField(max_length=255)
    career_interest = serializers.CharField(max_length=255, required=False)