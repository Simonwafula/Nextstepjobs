from rest_framework import serializers
from ..models import (
    AIJobAnalysis, AnonymousSearch, AIConfiguration, 
    AIUsageAnalytics, AIFeedback
)


class AIJobAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIJobAnalysis
        fields = [
            'id', 'job_description', 'job_title', 'company_name',
            'analysis_summary', 'detailed_analysis', 'required_qualifications',
            'required_skills', 'preferred_skills', 'responsibilities',
            'career_level', 'industry', 'growth_potential', 'work_environment',
            'salary_analysis', 'culture_indicators', 'company_values',
            'match_score', 'match_breakdown', 'strengths', 'gaps',
            'recommendations', 'improvement_suggestions', 'user_rating',
            'user_feedback', 'was_helpful', 'created_at'
        ]
        read_only_fields = [
            'id', 'analysis_summary', 'detailed_analysis', 'required_qualifications',
            'required_skills', 'preferred_skills', 'responsibilities',
            'career_level', 'industry', 'growth_potential', 'work_environment',
            'salary_analysis', 'culture_indicators', 'company_values',
            'match_score', 'match_breakdown', 'strengths', 'gaps',
            'recommendations', 'improvement_suggestions', 'created_at'
        ]


class AnonymousSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnonymousSearch
        fields = [
            'id', 'query', 'search_type', 'response', 'suggestions',
            'user_context', 'created_at'
        ]
        read_only_fields = ['id', 'response', 'suggestions', 'created_at']


class AIConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIConfiguration
        fields = [
            'id', 'name', 'description', 'config_type', 'model_name',
            'temperature', 'max_tokens', 'system_prompt', 'user_prompt_template',
            'available_variables', 'default_variables', 'response_format',
            'is_active', 'version', 'total_uses', 'average_response_time',
            'average_rating'
        ]


class AIFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIFeedback
        fields = [
            'id', 'content_type', 'content_id', 'rating', 'feedback_text',
            'accuracy', 'relevance', 'helpfulness', 'clarity', 'suggestions',
            'would_recommend', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class JobAnalysisRequestSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    job_description = serializers.CharField()
    job_title = serializers.CharField(required=False)
    company_name = serializers.CharField(required=False)


class AnonymousSearchRequestSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=2000)
    search_type = serializers.ChoiceField(
        choices=[
            ('general', 'General Career Advice'),
            ('career_path', 'Career Path Exploration'),
            ('skills', 'Skills Development'),
            ('industry', 'Industry Information'),
            ('salary', 'Salary Information'),
            ('education', 'Education Requirements'),
        ],
        default='general'
    )
    user_context = serializers.JSONField(required=False)