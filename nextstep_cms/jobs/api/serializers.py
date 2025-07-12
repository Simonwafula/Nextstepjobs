from rest_framework import serializers
from ..models import (
    Company, JobPosting, ProcessedJob, JobAlert, SavedJob, JobMatch
)


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'slug', 'description', 'website', 'logo_url',
            'industry', 'company_size', 'founded_year', 'headquarters',
            'locations', 'culture_description', 'benefits', 'remote_policy',
            'total_jobs_posted', 'hiring_frequency'
        ]
        read_only_fields = ['id', 'slug', 'total_jobs_posted', 'hiring_frequency']


class ProcessedJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessedJob
        fields = [
            'id', 'ai_summary', 'ai_industry_category', 'ai_role_level',
            'ai_company_culture', 'required_skills', 'preferred_skills',
            'technical_skills', 'soft_skills', 'education_requirements',
            'experience_requirements', 'certifications_required',
            'complexity_score', 'competitiveness_score', 'growth_potential',
            'keywords', 'tags', 'completeness_score', 'accuracy_score'
        ]


class JobPostingSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    processed_data = ProcessedJobSerializer(read_only=True)
    
    class Meta:
        model = JobPosting
        fields = [
            'id', 'source', 'source_url', 'title', 'company', 'description',
            'requirements', 'location', 'remote_friendly', 'work_arrangement',
            'job_type', 'experience_level', 'salary_min', 'salary_max',
            'salary_currency', 'salary_period', 'is_processed', 'quality_score',
            'posted_date', 'deadline', 'is_active', 'processed_data'
        ]
        read_only_fields = ['id', 'is_processed', 'quality_score']


class JobAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobAlert
        fields = [
            'id', 'name', 'keywords', 'excluded_keywords', 'location',
            'remote_only', 'job_types', 'experience_levels', 'industries',
            'min_salary', 'max_salary', 'email_notifications', 'frequency',
            'is_active', 'last_sent', 'total_matches'
        ]
        read_only_fields = ['id', 'last_sent', 'total_matches']


class SavedJobSerializer(serializers.ModelSerializer):
    job = JobPostingSerializer(read_only=True)
    job_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = SavedJob
        fields = [
            'id', 'job', 'job_id', 'category', 'notes', 'priority',
            'application_date', 'follow_up_date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class JobMatchSerializer(serializers.ModelSerializer):
    job = JobPostingSerializer(read_only=True)
    
    class Meta:
        model = JobMatch
        fields = [
            'id', 'job', 'overall_match_score', 'skills_match_score',
            'experience_match_score', 'location_match_score', 'education_match_score',
            'matching_skills', 'missing_skills', 'recommendations',
            'viewed', 'rating', 'feedback', 'calculated_at'
        ]


class JobSearchSerializer(serializers.Serializer):
    keywords = serializers.ListField(child=serializers.CharField(), required=False)
    location = serializers.CharField(required=False)
    remote_only = serializers.BooleanField(required=False)
    job_type = serializers.CharField(required=False)
    experience_level = serializers.CharField(required=False)
    industry = serializers.CharField(required=False)
    company = serializers.CharField(required=False)
    min_salary = serializers.IntegerField(required=False)
    max_salary = serializers.IntegerField(required=False)
    posted_days_ago = serializers.IntegerField(required=False)
    page = serializers.IntegerField(default=1)
    page_size = serializers.IntegerField(default=20)


class ScrapeJobsSerializer(serializers.Serializer):
    sources = serializers.ListField(
        child=serializers.ChoiceField(choices=['linkedin', 'indeed', 'brighter_monday']),
        required=True
    )
    search_terms = serializers.ListField(child=serializers.CharField(), required=True)
    location = serializers.CharField(required=False)
    limit_per_source = serializers.IntegerField(default=50)