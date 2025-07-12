import uuid
from django.db import models
from django.utils import timezone


class CareerPath(models.Model):
    """Predefined career paths and progressions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Information
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    
    # Categorization
    industry = models.CharField(max_length=255)
    field = models.CharField(max_length=255)
    level = models.CharField(
        max_length=20,
        choices=[
            ('entry', 'Entry Level'),
            ('junior', 'Junior'),
            ('mid', 'Mid Level'),
            ('senior', 'Senior'),
            ('lead', 'Lead'),
            ('executive', 'Executive'),
        ]
    )
    
    # Requirements
    typical_education = models.JSONField(default=list, blank=True)
    required_skills = models.JSONField(default=list, blank=True)
    preferred_skills = models.JSONField(default=list, blank=True)
    typical_experience = models.PositiveIntegerField(help_text="Years of experience typically required")
    
    # Career Information
    average_salary_min = models.PositiveIntegerField(null=True, blank=True)
    average_salary_max = models.PositiveIntegerField(null=True, blank=True)
    growth_outlook = models.CharField(
        max_length=20,
        choices=[
            ('declining', 'Declining'),
            ('stable', 'Stable'),
            ('growing', 'Growing'),
            ('high_growth', 'High Growth'),
        ],
        default='stable'
    )
    
    # Progression
    previous_roles = models.JSONField(default=list, blank=True)
    next_roles = models.JSONField(default=list, blank=True)
    alternative_paths = models.JSONField(default=list, blank=True)
    
    # Metadata
    demand_score = models.FloatField(default=0.0)  # Market demand
    competition_score = models.FloatField(default=0.0)  # Competition level
    satisfaction_score = models.FloatField(default=0.0)  # Job satisfaction
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'career_paths'
        ordering = ['industry', 'level', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.level})"


class CareerAdviceSession(models.Model):
    """Individual career advice sessions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey('profiles.UserProfile', on_delete=models.CASCADE, related_name='advice_sessions')
    
    # Session Information
    query = models.TextField()
    session_type = models.CharField(
        max_length=20,
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
    
    # AI Response
    advice = models.TextField()
    recommendations = models.JSONField(default=list, blank=True)
    action_items = models.JSONField(default=list, blank=True)
    resources = models.JSONField(default=list, blank=True)
    
    # Session Context
    context_data = models.JSONField(default=dict, blank=True)  # User context at time of session
    follow_up_questions = models.JSONField(default=list, blank=True)
    
    # User Feedback
    rating = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-5 stars
    feedback = models.TextField(null=True, blank=True)
    was_helpful = models.BooleanField(null=True, blank=True)
    
    # Session Metadata
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    tokens_used = models.PositiveIntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'career_advice_sessions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Advice for {self.user_profile.name} - {self.session_type}"


class CareerGoal(models.Model):
    """User-defined career goals and tracking"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey('profiles.UserProfile', on_delete=models.CASCADE, related_name='career_goals')
    
    # Goal Information
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(
        max_length=30,
        choices=[
            ('role_transition', 'Role Transition'),
            ('skill_development', 'Skill Development'),
            ('salary_increase', 'Salary Increase'),
            ('education', 'Education/Certification'),
            ('networking', 'Professional Networking'),
            ('work_life_balance', 'Work-Life Balance'),
            ('leadership', 'Leadership Development'),
            ('entrepreneurship', 'Entrepreneurship'),
        ]
    )
    
    # Timeline
    target_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    completion_date = models.DateField(null=True, blank=True)
    
    # Progress Tracking
    progress_percentage = models.PositiveSmallIntegerField(default=0)  # 0-100
    milestones = models.JSONField(default=list, blank=True)
    completed_milestones = models.JSONField(default=list, blank=True)
    
    # Goal Details
    priority = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ],
        default='medium'
    )
    difficulty = models.CharField(
        max_length=10,
        choices=[
            ('easy', 'Easy'),
            ('medium', 'Medium'),
            ('hard', 'Hard'),
        ],
        default='medium'
    )
    
    # Resources and Actions
    action_plan = models.JSONField(default=list, blank=True)
    resources_needed = models.JSONField(default=list, blank=True)
    barriers = models.JSONField(default=list, blank=True)
    
    # Tracking
    notes = models.TextField(null=True, blank=True)
    last_reviewed = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'career_goals'
        ordering = ['-priority', 'target_date']
    
    def __str__(self):
        return f"{self.user_profile.name} - {self.title}"


class SkillGapAnalysis(models.Model):
    """Analysis of skill gaps for specific career paths"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey('profiles.UserProfile', on_delete=models.CASCADE, related_name='skill_gap_analyses')
    target_roles = models.JSONField(default=list)  # List of target role names
    
    # Analysis Results
    current_skills = models.JSONField(default=list, blank=True)
    required_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    skill_recommendations = models.JSONField(default=list, blank=True)
    
    # Gap Metrics
    overall_gap_percentage = models.FloatField()
    critical_gaps = models.JSONField(default=list, blank=True)
    strength_areas = models.JSONField(default=list, blank=True)
    
    # Recommendations
    learning_path = models.JSONField(default=list, blank=True)
    estimated_learning_time = models.PositiveIntegerField(null=True, blank=True)  # In hours
    priority_skills = models.JSONField(default=list, blank=True)
    
    # Resources
    recommended_courses = models.JSONField(default=list, blank=True)
    recommended_certifications = models.JSONField(default=list, blank=True)
    practice_projects = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'skill_gap_analyses'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Skill Gap Analysis for {self.user_profile.name} - {len(self.target_roles)} roles"


class MarketInsight(models.Model):
    """Market insights and trends for industries/roles"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Scope
    insight_type = models.CharField(
        max_length=20,
        choices=[
            ('industry', 'Industry'),
            ('role', 'Role/Position'),
            ('skill', 'Skill'),
            ('location', 'Location'),
            ('salary', 'Salary Trends'),
        ]
    )
    category = models.CharField(max_length=255)  # Industry name, role name, etc.
    
    # Insight Data
    title = models.CharField(max_length=255)
    summary = models.TextField()
    detailed_analysis = models.TextField()
    
    # Metrics
    demand_trend = models.CharField(
        max_length=20,
        choices=[
            ('declining', 'Declining'),
            ('stable', 'Stable'),
            ('growing', 'Growing'),
            ('high_growth', 'High Growth'),
        ]
    )
    salary_trend = models.CharField(
        max_length=20,
        choices=[
            ('decreasing', 'Decreasing'),
            ('stable', 'Stable'),
            ('increasing', 'Increasing'),
            ('rapidly_increasing', 'Rapidly Increasing'),
        ]
    )
    
    # Data Points
    key_statistics = models.JSONField(default=dict, blank=True)
    trending_skills = models.JSONField(default=list, blank=True)
    top_companies = models.JSONField(default=list, blank=True)
    geographic_hotspots = models.JSONField(default=list, blank=True)
    
    # Future Outlook
    future_outlook = models.TextField(null=True, blank=True)
    predicted_changes = models.JSONField(default=list, blank=True)
    opportunities = models.JSONField(default=list, blank=True)
    challenges = models.JSONField(default=list, blank=True)
    
    # Metadata
    data_sources = models.JSONField(default=list, blank=True)
    confidence_score = models.FloatField(default=0.0)
    
    # Validity
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    is_current = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'market_insights'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['insight_type', 'category']),
            models.Index(fields=['is_current', 'valid_from']),
        ]
    
    def __str__(self):
        return f"{self.insight_type.title()} Insight: {self.title}"


class CareerRecommendation(models.Model):
    """AI-generated career recommendations for users"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey('profiles.UserProfile', on_delete=models.CASCADE, related_name='career_recommendations')
    
    # Recommendation Type
    recommendation_type = models.CharField(
        max_length=30,
        choices=[
            ('career_path', 'Career Path'),
            ('skill_development', 'Skill Development'),
            ('education', 'Education/Training'),
            ('job_search', 'Job Search Strategy'),
            ('networking', 'Networking'),
            ('salary_negotiation', 'Salary Negotiation'),
            ('interview_prep', 'Interview Preparation'),
        ]
    )
    
    # Recommendation Content
    title = models.CharField(max_length=255)
    description = models.TextField()
    detailed_advice = models.TextField()
    
    # Action Items
    action_items = models.JSONField(default=list, blank=True)
    resources = models.JSONField(default=list, blank=True)
    timeline = models.CharField(max_length=50, null=True, blank=True)
    
    # Personalization
    personalization_factors = models.JSONField(default=dict, blank=True)
    confidence_score = models.FloatField()
    priority_score = models.FloatField()
    
    # User Interaction
    viewed = models.BooleanField(default=False)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)
    implemented = models.BooleanField(default=False)
    
    # Status
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'career_recommendations'
        ordering = ['-priority_score', '-created_at']
    
    def __str__(self):
        return f"Recommendation for {self.user_profile.name}: {self.title}"