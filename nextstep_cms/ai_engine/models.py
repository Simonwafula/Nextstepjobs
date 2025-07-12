import uuid
from django.db import models
from django.utils import timezone


class AIJobAnalysis(models.Model):
    """AI-powered job analysis results"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey('profiles.UserProfile', on_delete=models.CASCADE, related_name='job_analyses')
    
    # Input Data
    job_description = models.TextField()
    job_title = models.CharField(max_length=500, null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    
    # AI Analysis Results
    analysis_summary = models.TextField()
    detailed_analysis = models.JSONField(default=dict, blank=True)
    
    # Extracted Information
    required_qualifications = models.JSONField(default=dict, blank=True)
    required_skills = models.JSONField(default=list, blank=True)
    preferred_skills = models.JSONField(default=list, blank=True)
    responsibilities = models.JSONField(default=list, blank=True)
    
    # Job Characteristics
    career_level = models.CharField(max_length=50, null=True, blank=True)
    industry = models.CharField(max_length=255, null=True, blank=True)
    growth_potential = models.CharField(max_length=100, null=True, blank=True)
    work_environment = models.CharField(max_length=100, null=True, blank=True)
    
    # Salary Analysis
    salary_analysis = models.JSONField(default=dict, blank=True)
    
    # Company Culture Analysis
    culture_indicators = models.JSONField(default=list, blank=True)
    company_values = models.JSONField(default=list, blank=True)
    
    # Match Assessment
    match_score = models.FloatField()
    match_breakdown = models.JSONField(default=dict, blank=True)
    strengths = models.JSONField(default=list, blank=True)
    gaps = models.JSONField(default=list, blank=True)
    
    # Recommendations
    recommendations = models.JSONField(default=list, blank=True)
    improvement_suggestions = models.JSONField(default=list, blank=True)
    
    # AI Metadata
    ai_model_used = models.CharField(max_length=100, default='gpt-4')
    tokens_used = models.PositiveIntegerField(default=0)
    processing_time = models.FloatField(null=True, blank=True)  # In seconds
    confidence_score = models.FloatField(null=True, blank=True)
    
    # User Feedback
    user_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    user_feedback = models.TextField(null=True, blank=True)
    was_helpful = models.BooleanField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'ai_job_analyses'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Job Analysis for {self.user_profile.name} - {self.job_title or 'Untitled'}"


class AnonymousSearch(models.Model):
    """Anonymous career search queries and responses"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Search Information
    query = models.TextField()
    search_type = models.CharField(
        max_length=20,
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
    
    # AI Response
    response = models.TextField()
    suggestions = models.JSONField(default=list, blank=True)
    
    # Search Context
    user_context = models.JSONField(default=dict, blank=True)  # Any provided context
    search_metadata = models.JSONField(default=dict, blank=True)
    
    # AI Processing
    ai_model_used = models.CharField(max_length=100, default='gpt-4')
    tokens_used = models.PositiveIntegerField(default=0)
    processing_time = models.FloatField(null=True, blank=True)
    
    # Analytics
    session_id = models.CharField(max_length=255, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    referrer = models.URLField(null=True, blank=True)
    
    # Quality Metrics
    response_quality_score = models.FloatField(null=True, blank=True)
    user_engagement_score = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'anonymous_searches'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['search_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Anonymous Search: {self.search_type} - {self.query[:50]}..."


class AIConfiguration(models.Model):
    """Configuration settings for AI models and prompts"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Configuration Identity
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    config_type = models.CharField(
        max_length=30,
        choices=[
            ('job_analysis', 'Job Analysis'),
            ('career_advice', 'Career Advice'),
            ('skill_recommendation', 'Skill Recommendation'),
            ('market_analysis', 'Market Analysis'),
            ('resume_review', 'Resume Review'),
        ]
    )
    
    # AI Model Settings
    model_name = models.CharField(max_length=100, default='gpt-4')
    temperature = models.FloatField(default=0.7)
    max_tokens = models.PositiveIntegerField(default=2000)
    
    # Prompts
    system_prompt = models.TextField()
    user_prompt_template = models.TextField()
    
    # Prompt Variables
    available_variables = models.JSONField(default=list, blank=True)
    default_variables = models.JSONField(default=dict, blank=True)
    
    # Quality Settings
    response_format = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Plain Text'),
            ('json', 'JSON'),
            ('markdown', 'Markdown'),
        ],
        default='text'
    )
    
    # Usage and Performance
    total_uses = models.PositiveIntegerField(default=0)
    average_response_time = models.FloatField(null=True, blank=True)
    average_rating = models.FloatField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    version = models.CharField(max_length=20, default='1.0')
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_configurations'
        ordering = ['config_type', 'name']
    
    def __str__(self):
        return f"{self.config_type}: {self.name}"


class AIUsageAnalytics(models.Model):
    """Analytics for AI feature usage"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Usage Information
    feature_type = models.CharField(
        max_length=30,
        choices=[
            ('job_analysis', 'Job Analysis'),
            ('career_advice', 'Career Advice'),
            ('anonymous_search', 'Anonymous Search'),
            ('skill_gap_analysis', 'Skill Gap Analysis'),
            ('job_matching', 'Job Matching'),
        ]
    )
    user_profile = models.ForeignKey('profiles.UserProfile', on_delete=models.SET_NULL, null=True, blank=True)
    
    # AI Model Information
    ai_model = models.CharField(max_length=100)
    tokens_consumed = models.PositiveIntegerField()
    processing_time = models.FloatField()  # In seconds
    
    # Quality Metrics
    response_quality = models.FloatField(null=True, blank=True)
    user_satisfaction = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-5
    
    # Usage Context
    session_data = models.JSONField(default=dict, blank=True)
    error_occurred = models.BooleanField(default=False)
    error_details = models.TextField(null=True, blank=True)
    
    # Cost Analysis
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'ai_usage_analytics'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['feature_type', 'timestamp']),
            models.Index(fields=['user_profile', 'timestamp']),
        ]
    
    def __str__(self):
        user_name = self.user_profile.name if self.user_profile else "Anonymous"
        return f"{self.feature_type} - {user_name} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class AIFeedback(models.Model):
    """User feedback for AI-generated content"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey('profiles.UserProfile', on_delete=models.CASCADE, null=True, blank=True)
    
    # Content Reference
    content_type = models.CharField(
        max_length=30,
        choices=[
            ('job_analysis', 'Job Analysis'),
            ('career_advice', 'Career Advice'),
            ('skill_recommendation', 'Skill Recommendation'),
            ('job_match', 'Job Match'),
            ('anonymous_search', 'Anonymous Search'),
        ]
    )
    content_id = models.UUIDField()  # Reference to the specific AI-generated content
    
    # Feedback Data
    rating = models.PositiveSmallIntegerField()  # 1-5 stars
    feedback_text = models.TextField(null=True, blank=True)
    
    # Specific Feedback Categories
    accuracy = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-5
    relevance = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-5
    helpfulness = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-5
    clarity = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-5
    
    # Improvement Suggestions
    suggestions = models.TextField(null=True, blank=True)
    would_recommend = models.BooleanField(null=True, blank=True)
    
    # Metadata
    feedback_metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'ai_feedback'
        ordering = ['-created_at']
        unique_together = ['user_profile', 'content_type', 'content_id']
    
    def __str__(self):
        user_name = self.user_profile.name if self.user_profile else "Anonymous"
        return f"Feedback from {user_name} - {self.content_type} ({self.rating}/5)"