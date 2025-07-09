# processors/models.py
from pydantic import BaseModel, constr, conint
from typing import List, Optional

class EducationRequirement(BaseModel):
    level: constr(pattern=r'^(diploma|certificate|associate|bachelor|master|phd|professional_license|none_specified)$')
    field: str
    requirement_type: constr(pattern=r'^(required|preferred|equivalent_experience_accepted)$')
    years_experience_in_lieu: Optional[conint(ge=0)] = None

class SkillProficiency(BaseModel):
    skill: str
    level: constr(pattern=r'^(beginner|intermediate|advanced|expert)$')
    years_required: Optional[conint(ge=0)] = None
    requirement_type: constr(pattern=r'^(required|preferred)$')

class Certification(BaseModel):
    name: str
    issuing_body: str
    requirement_type: constr(pattern=r'^(required|preferred)$')
    expiry_consideration: constr(pattern=r'^(must_be_current|no_expiry_mentioned)$')

class JobClassification(BaseModel):
    job_title_raw: str
    job_title_normalized: str
    job_function: str
    seniority_level: str
    experience_years_min: Optional[conint(ge=0)] = None
    experience_years_max: Optional[conint(ge=0)] = None
    industry_sector: str

class LocationWork(BaseModel):
    work_location_type: str
    travel_requirements: str
    geographic_scope: str

class SkillsTaxonomy(BaseModel):
    programming_languages: List[str] = []
    software_tools: List[str] = []
    frameworks_libraries: List[str] = []
    databases: List[str] = []
    cloud_platforms: List[str] = []
    methodologies: List[str] = []
    domain_specific_tools: List[str] = []
    soft_skills: List[str] = []
    skill_proficiencies: List[SkillProficiency] = []

class CareerProgression(BaseModel):
    career_stage: str
    advancement_potential: str
    prerequisite_roles: List[str] = []
    next_level_roles: List[str] = []
    career_transition_friendly: bool

class CompensationBenefits(BaseModel):
    salary_min: Optional[conint(ge=0)] = None
    salary_max: Optional[conint(ge=0)] = None
    salary_currency: str
    salary_type: str
    equity_mentioned: bool
    bonus_structure: str
    benefits_quality: str
    professional_development_budget: bool

class MarketIntelligence(BaseModel):
    urgency_indicators: str
    demand_signals: str
    company_growth_stage: str
    automation_risk: str
    remote_work_maturity: str

class WorkEnvironment(BaseModel):
    team_size: Optional[conint(ge=0)] = None
    collaboration_level: str
    client_interaction: str
    decision_making_level: str
    work_pace: str

class JobStructured(BaseModel):
    id: int
    company_name: str
    location: str
    post_date: str
    education_requirements: List[EducationRequirement]
    job_classification: JobClassification
    location_and_work: LocationWork
    skills: SkillsTaxonomy
    certifications: List[Certification]
    career_progression: CareerProgression
    compensation: CompensationBenefits
    market_intelligence: MarketIntelligence
    work_environment: WorkEnvironment
