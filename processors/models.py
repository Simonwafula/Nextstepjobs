# processors/models.py
"""Data models used in the legacy job processing pipeline.

These were previously implemented using ``pydantic.BaseModel`` but the
project has since migrated to a Django/Wagtail CRX architecture.  To avoid
requiring Pydantic while still providing simple structured data containers,
the models are now lightweight ``dataclasses``.
"""

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class EducationRequirement:
    level: str
    field: str
    requirement_type: str
    years_experience_in_lieu: Optional[int] = None

@dataclass
class SkillProficiency:
    skill: str
    level: str
    years_required: Optional[int] = None
    requirement_type: str

@dataclass
class Certification:
    name: str
    issuing_body: str
    requirement_type: str
    expiry_consideration: str

@dataclass
class JobClassification:
    job_title_raw: str
    job_title_normalized: str
    job_function: str
    seniority_level: str
    experience_years_min: Optional[int] = None
    experience_years_max: Optional[int] = None
    industry_sector: str

@dataclass
class LocationWork:
    work_location_type: str
    travel_requirements: str
    geographic_scope: str

@dataclass
class SkillsTaxonomy:
    programming_languages: List[str] = field(default_factory=list)
    software_tools: List[str] = field(default_factory=list)
    frameworks_libraries: List[str] = field(default_factory=list)
    databases: List[str] = field(default_factory=list)
    cloud_platforms: List[str] = field(default_factory=list)
    methodologies: List[str] = field(default_factory=list)
    domain_specific_tools: List[str] = field(default_factory=list)
    soft_skills: List[str] = field(default_factory=list)
    skill_proficiencies: List[SkillProficiency] = field(default_factory=list)

@dataclass
class CareerProgression:
    career_stage: str
    advancement_potential: str
    prerequisite_roles: List[str] = field(default_factory=list)
    next_level_roles: List[str] = field(default_factory=list)
    career_transition_friendly: bool

@dataclass
class CompensationBenefits:
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str
    salary_type: str
    equity_mentioned: bool
    bonus_structure: str
    benefits_quality: str
    professional_development_budget: bool

@dataclass
class MarketIntelligence:
    urgency_indicators: str
    demand_signals: str
    company_growth_stage: str
    automation_risk: str
    remote_work_maturity: str

@dataclass
class WorkEnvironment:
    team_size: Optional[int] = None
    collaboration_level: str
    client_interaction: str
    decision_making_level: str
    work_pace: str

@dataclass
class JobStructured:
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
