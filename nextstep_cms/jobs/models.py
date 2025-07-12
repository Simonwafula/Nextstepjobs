import uuid
from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField


class Company(models.Model):
    """Company information for job postings"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Information
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    logo_url = models.URLField(null=True, blank=True)
    
    # Company Details
    industry = models.CharField(max_length=255, null=True, blank=True)
    company_size = models.CharField(
        max_length=20,
        choices=[
            ('startup', '1-10 employees'),
            ('small', '11-50 employees'),
            ('medium', '51-200 employees'),
            ('large', '201-1000 employees'),
            ('enterprise', '1000+ employees'),
        ],
        null=True, blank=True
    )
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    
    # Location
    headquarters = models.CharField(max_length=255, null=True, blank=True)
    locations = models.JSONField(default=list, blank=True)
    
    # Culture & Benefits
    culture_description = models.TextField(null=True, blank=True)
    benefits = models.JSONField(default=list, blank=True)
    remote_policy = models.CharField(
        max_length=20,
        choices=[
            ('on_site', 'On-site only'),
            ('remote', 'Remote-first'),
            ('hybrid', 'Hybrid'),
            ('flexible', 'Flexible'),
        ],
        null=True, blank=True
    )
    
    # Statistics
    total_jobs_posted = models.PositiveIntegerField(default=0)
    hiring_frequency = models.FloatField(default=0.0)  # Jobs per month
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'companies'
        ordering = ['name']
        verbose_name_plural = 'Companies'
    
    def __str__(self):
        return self.name


class JobPosting(models.Model):
    """Raw job postings from various sources"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Source Information
    source = models.CharField(
        max_length=50,
        choices=[
            ('linkedin', 'LinkedIn'),
            ('indeed', 'Indeed'),
            ('brighter_monday', 'BrighterMonday'),
            ('glassdoor', 'Glassdoor'),
            ('company_website', 'Company Website'),
            ('manual', 'Manual Entry'),
        ]
    )
    external_id = models.CharField(max_length=255, null=True, blank=True)
    source_url = models.URLField()
    
    # Basic Job Information
    title = models.CharField(max_length=500)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='job_postings')
    description = models.TextField()
    requirements = models.TextField(null=True, blank=True)
    
    # Location & Remote
    location = models.CharField(max_length=255, null=True, blank=True)
    remote_friendly = models.BooleanField(default=False)
    work_arrangement = models.CharField(
        max_length=20,
        choices=[
            ('on_site', 'On-site'),
            ('remote', 'Remote'),
            ('hybrid', 'Hybrid'),
        ],
        default='on_site'
    )
    
    # Job Details
    job_type = models.CharField(
        max_length=20,
        choices=[
            ('full_time', 'Full-time'),
            ('part_time', 'Part-time'),
            ('contract', 'Contract'),
            ('freelance', 'Freelance'),
            ('internship', 'Internship'),
        ],
        default='full_time'
    )
    experience_level = models.CharField(
        max_length=20,
        choices=[
            ('entry', 'Entry Level'),
            ('junior', 'Junior'),
            ('mid', 'Mid Level'),
            ('senior', 'Senior'),
            ('lead', 'Lead'),
            ('principal', 'Principal'),
            ('director', 'Director'),
        ],
        null=True, blank=True
    )
    
    # Salary Information
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=10, default='USD')
    salary_period = models.CharField(
        max_length=20,
        choices=[
            ('hourly', 'Hourly'),
            ('monthly', 'Monthly'),
            ('annual', 'Annual'),
        ],
        default='annual'
    )
    
    # Processing Status
    is_processed = models.BooleanField(default=False)
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    quality_score = models.FloatField(null=True, blank=True)
    
    # Timestamps
    posted_date = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    scraped_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_expired = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'job_postings'
        ordering = ['-posted_date', '-created_at']
        indexes = [
            models.Index(fields=['source', 'external_id']),
            models.Index(fields=['is_active', 'is_processed']),
            models.Index(fields=['posted_date']),
        ]
    
    def __str__(self):
        return f"{self.title} at {self.company.name}"


class ProcessedJob(models.Model):
    """AI-processed job postings with enhanced data"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_job = models.OneToOneField(JobPosting, on_delete=models.CASCADE, related_name='processed_data')
    
    # AI-Enhanced Information
    ai_summary = models.TextField(null=True, blank=True)
    ai_industry_category = models.CharField(max_length=255, null=True, blank=True)
    ai_role_level = models.CharField(max_length=50, null=True, blank=True)
    ai_company_culture = models.TextField(null=True, blank=True)
    
    # Extracted Skills and Requirements
    required_skills = models.JSONField(default=list, blank=True)
    preferred_skills = models.JSONField(default=list, blank=True)
    technical_skills = models.JSONField(default=list, blank=True)
    soft_skills = models.JSONField(default=list, blank=True)
    
    # Requirements Analysis
    education_requirements = models.JSONField(default=dict, blank=True)
    experience_requirements = models.JSONField(default=dict, blank=True)
    certifications_required = models.JSONField(default=list, blank=True)
    
    # Job Analytics
    complexity_score = models.FloatField(null=True, blank=True)
    competitiveness_score = models.FloatField(null=True, blank=True)
    growth_potential = models.CharField(max_length=50, null=True, blank=True)
    
    # Matching Data
    keywords = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    # Quality Metrics
    completeness_score = models.FloatField(null=True, blank=True)
    accuracy_score = models.FloatField(null=True, blank=True)
    
    processed_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'processed_jobs'
        ordering = ['-processed_at']
    
    def __str__(self):
        return f"Processed: {self.original_job.title}"


class JobAlert(models.Model):
    """User job alerts and notifications"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey('profiles.UserProfile', on_delete=models.CASCADE, related_name='job_alerts')
    
    # Alert Configuration
    name = models.CharField(max_length=255)
    keywords = models.JSONField(default=list, blank=True)
    excluded_keywords = models.JSONField(default=list, blank=True)
    
    # Filters
    location = models.CharField(max_length=255, null=True, blank=True)
    remote_only = models.BooleanField(default=False)
    job_types = models.JSONField(default=list, blank=True)
    experience_levels = models.JSONField(default=list, blank=True)
    industries = models.JSONField(default=list, blank=True)
    
    # Salary Filters
    min_salary = models.PositiveIntegerField(null=True, blank=True)
    max_salary = models.PositiveIntegerField(null=True, blank=True)
    
    # Notification Settings
    email_notifications = models.BooleanField(default=True)
    frequency = models.CharField(
        max_length=20,
        choices=[
            ('instant', 'Instant'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
        ],
        default='daily'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    last_sent = models.DateTimeField(null=True, blank=True)
    total_matches = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'job_alerts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user_profile.name} - {self.name}"


class SavedJob(models.Model):
    """Jobs saved by users"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey('profiles.UserProfile', on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE)
    
    # Categorization
    category = models.CharField(
        max_length=20,
        choices=[
            ('interested', 'Interested'),
            ('applied', 'Applied'),
            ('interviewing', 'Interviewing'),
            ('rejected', 'Rejected'),
            ('declined', 'Declined'),
            ('reference', 'Reference'),
        ],
        default='interested'
    )
    
    # User Notes
    notes = models.TextField(null=True, blank=True)
    priority = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ],
        default='medium'
    )
    
    # Application Tracking
    application_date = models.DateTimeField(null=True, blank=True)
    follow_up_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'saved_jobs'
        unique_together = ['user_profile', 'job']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user_profile.name} saved {self.job.title}"


class JobMatch(models.Model):
    """AI-calculated job matches for users"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey('profiles.UserProfile', on_delete=models.CASCADE, related_name='job_matches')
    job = models.ForeignKey(ProcessedJob, on_delete=models.CASCADE, related_name='user_matches')
    
    # Match Scores
    overall_match_score = models.FloatField()
    skills_match_score = models.FloatField(default=0.0)
    experience_match_score = models.FloatField(default=0.0)
    location_match_score = models.FloatField(default=0.0)
    education_match_score = models.FloatField(default=0.0)
    
    # Match Details
    matching_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    
    # User Interaction
    viewed = models.BooleanField(default=False)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-5 stars
    feedback = models.TextField(null=True, blank=True)
    
    calculated_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'job_matches'
        unique_together = ['user_profile', 'job']
        ordering = ['-overall_match_score', '-calculated_at']
        indexes = [
            models.Index(fields=['user_profile', 'overall_match_score']),
        ]
    
    def __str__(self):
        return f"{self.user_profile.name} - {self.job.original_job.title} ({self.overall_match_score:.2f})"