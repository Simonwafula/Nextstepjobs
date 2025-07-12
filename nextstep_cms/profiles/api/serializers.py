from rest_framework import serializers
from ..models import UserProfile, Skill, UserSkill, Experience, Education


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'category', 'description', 'popularity_score']


class UserSkillSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)
    skill_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = UserSkill
        fields = ['id', 'skill', 'skill_id', 'proficiency', 'years_experience', 'is_primary']


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = [
            'id', 'job_title', 'company_name', 'company_size', 'start_date', 'end_date',
            'is_current', 'description', 'achievements', 'technologies_used',
            'location', 'remote_work'
        ]


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = [
            'id', 'institution_name', 'degree_type', 'field_of_study', 'start_date',
            'end_date', 'is_current', 'gpa', 'honors', 'description', 'relevant_coursework'
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    skills = UserSkillSerializer(many=True, read_only=True)
    experiences = ExperienceSerializer(many=True, read_only=True)
    education = EducationSerializer(many=True, read_only=True)
    experience_level = serializers.CharField(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'name', 'email', 'phone', 'education_level', 'field_of_study',
            'graduation_year', 'experience_years', 'current_role', 'current_company',
            'current_location', 'preferred_locations', 'remote_work_preference',
            'career_interests', 'target_roles', 'salary_expectations',
            'profile_completed', 'onboarding_completed', 'created_at', 'updated_at',
            'last_active', 'experience_level', 'skills', 'experiences', 'education'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserProfileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'name', 'email', 'phone', 'education_level', 'field_of_study',
            'graduation_year', 'experience_years', 'current_role', 'current_company',
            'current_location', 'preferred_locations', 'remote_work_preference',
            'career_interests', 'target_roles', 'salary_expectations'
        ]