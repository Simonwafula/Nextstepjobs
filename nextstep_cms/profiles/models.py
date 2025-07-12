import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """Extended user profile for career guidance"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Basic Information
    name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    
    # Education
    education_level = models.CharField(
        max_length=100,
        choices=[
            ('high_school', 'High School'),
            ('associates', 'Associate Degree'),
            ('bachelors', 'Bachelor\'s Degree'),
            ('masters', 'Master\'s Degree'),
            ('phd', 'PhD/Doctorate'),
            ('certification', 'Professional Certification'),
            ('bootcamp', 'Bootcamp/Training Program'),
        ],
        default='bachelors'
    )
    field_of_study = models.CharField(max_length=255, null=True, blank=True)
    graduation_year = models.PositiveIntegerField(null=True, blank=True)
    
    # Experience
    experience_years = models.PositiveIntegerField(default=0)
    current_role = models.CharField(max_length=255, null=True, blank=True)
    current_company = models.CharField(max_length=255, null=True, blank=True)
    
    # Location Preferences
    current_location = models.CharField(max_length=255, null=True, blank=True)
    preferred_locations = models.JSONField(default=list, blank=True)
    remote_work_preference = models.CharField(
        max_length=20,
        choices=[
            ('on_site', 'On-site only'),
            ('remote', 'Remote only'),
            ('hybrid', 'Hybrid'),
            ('flexible', 'Flexible'),
        ],
        default='flexible'
    )
    
    # Career Information
    career_interests = models.JSONField(default=list, blank=True)
    target_roles = models.JSONField(default=list, blank=True)
    salary_expectations = models.JSONField(default=dict, blank=True)  # {min, max, currency}
    
    # Profile Completeness
    profile_completed = models.BooleanField(default=False)
    onboarding_completed = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_active = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'user_profiles'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.current_role or 'Job Seeker'}"
    
    @property
    def skills_list(self):
        """Get all skills for this user"""
        return self.skills.all()
    
    @property
    def experience_level(self):
        """Calculate experience level based on years"""
        if self.experience_years == 0:
            return "Entry Level"
        elif self.experience_years <= 2:
            return "Junior"
        elif self.experience_years <= 5:
            return "Mid Level"
        elif self.experience_years <= 8:
            return "Senior"
        else:
            return "Expert"


class Skill(models.Model):
    """Skills that users can possess"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('technical', 'Technical'),
            ('soft_skills', 'Soft Skills'),
            ('language', 'Language'),
            ('certification', 'Certification'),
            ('tool', 'Tool/Software'),
            ('framework', 'Framework'),
            ('domain', 'Domain Knowledge'),
        ],
        default='technical'
    )
    description = models.TextField(null=True, blank=True)
    popularity_score = models.FloatField(default=0.0)  # For ranking skills
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'skills'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserSkill(models.Model):
    """Many-to-many relationship between users and skills with proficiency"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    
    proficiency = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert'),
        ],
        default='intermediate'
    )
    years_experience = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)  # Key skill for the user
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_skills'
        unique_together = ['user_profile', 'skill']
        ordering = ['-is_primary', '-proficiency', 'skill__name']
    
    def __str__(self):
        return f"{self.user_profile.name} - {self.skill.name} ({self.proficiency})"


class Experience(models.Model):
    """Work experience entries for users"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='experiences')
    
    # Job Details
    job_title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
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
    
    # Duration
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    
    # Details
    description = models.TextField(null=True, blank=True)
    achievements = models.JSONField(default=list, blank=True)
    technologies_used = models.JSONField(default=list, blank=True)
    
    # Location
    location = models.CharField(max_length=255, null=True, blank=True)
    remote_work = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_experiences'
        ordering = ['-is_current', '-start_date']
    
    def __str__(self):
        return f"{self.user_profile.name} - {self.job_title} at {self.company_name}"


class Education(models.Model):
    """Education entries for users"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='education')
    
    # Institution Details
    institution_name = models.CharField(max_length=255)
    degree_type = models.CharField(
        max_length=50,
        choices=[
            ('high_school', 'High School Diploma'),
            ('associates', 'Associate Degree'),
            ('bachelors', 'Bachelor\'s Degree'),
            ('masters', 'Master\'s Degree'),
            ('phd', 'PhD/Doctorate'),
            ('certification', 'Professional Certification'),
            ('bootcamp', 'Bootcamp'),
            ('online_course', 'Online Course'),
        ]
    )
    field_of_study = models.CharField(max_length=255)
    
    # Duration
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    
    # Academic Performance
    gpa = models.FloatField(null=True, blank=True)
    honors = models.CharField(max_length=255, null=True, blank=True)
    
    # Additional Details
    description = models.TextField(null=True, blank=True)
    relevant_coursework = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_education'
        ordering = ['-is_current', '-start_date']
    
    def __str__(self):
        return f"{self.user_profile.name} - {self.degree_type} in {self.field_of_study}"