from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from typing import List
import uuid
from datetime import datetime, timedelta
from emergentintegrations.llm.chat import LlmChat, UserMessage
import asyncio
from scrapers.base_scraper import BaseScraper
from scrapers.indeed_scraper import IndeedScraper
from scrapers.linkedin_scraper import LinkedInScraper
from scrapers.brighter_monday_scraper import BrighterMondayScraper
from processors.pipeline2 import JobProcessor, process_job_batch

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix

app = FastAPI(
    title="NextStep Job Advisory API",
    description="Comprehensive job advisory platform for students, graduates, and professionals",
    version="2.0.0"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize scrapers
scrapers = {
    'indeed': IndeedScraper(),
    'linkedin': LinkedInScraper(),
    'brightermonday': BrighterMondayScraper()
}


# Define Models
class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    education_level: str  # High School, Bachelor's, Master's, PhD, etc.
    field_of_study: Optional[str] = None
    skills: List[str] = []
    experience_years: int = 0
    current_role: Optional[str] = None
    career_interests: List[str] = []
    preferred_locations: List[str] = []
    salary_expectations: Optional[Dict] = None
    job_preferences: Dict = Field(default_factory=dict)  # remote, job_type, etc.
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserProfileCreate(BaseModel):
    name: str
    email: str
    education_level: str
    field_of_study: Optional[str] = None
    skills: List[str] = []
    experience_years: int = 0
    current_role: Optional[str] = None
    career_interests: List[str] = []
    preferred_locations: List[str] = []
    salary_expectations: Optional[Dict] = None
    job_preferences: Dict = Field(default_factory=dict)

class JobSearchRequest(BaseModel):
    search_terms: List[str]
    location: Optional[str] = None
    sources: List[str] = Field(default=['indeed', 'brightermonday'])  # Available scrapers
    limit_per_source: int = 25

class JobFilterRequest(BaseModel):
    industry: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    location: Optional[str] = None
    skills: Optional[List[str]] = None
    remote_friendly: Optional[bool] = None
    company: Optional[str] = None
    posted_days_ago: Optional[int] = None

class SavedJob(BaseModel):
    user_id: str
    job_id: str
    saved_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    application_status: str = "interested"  # interested, applied, interviewing, rejected, hired

class JobAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    search_criteria: Dict
    frequency: str = "daily"  # daily, weekly
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MarketAnalysisRequest(BaseModel):
    industry: Optional[str] = None
    location: Optional[str] = None
    job_title: Optional[str] = None
    skills: Optional[List[str]] = None
    time_period: int = 30  # days

class JobAnalysisRequest(BaseModel):
    user_id: str
    job_description: str

class JobAnalysisResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: str
    job_description: str
    analysis: Dict[str, Any]
    recommendations: List[str]
    match_score: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str
class CareerAdviceRequest(BaseModel):
    user_id: str
    query: str

# Add your routes to the router instead of directly to app
class CareerAdviceResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    query: str
    advice: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Helper function to get OpenAI response
async def get_ai_response(system_message: str, user_message: str) -> str:
    try:
        chat = LlmChat(
            api_key=os.environ.get('OPENAI_API_KEY'),
            session_id=str(uuid.uuid4()),
            system_message=system_message
        ).with_model("openai", "gpt-4o")

        message = UserMessage(text=user_message)
        response = await chat.send_message(message)
        return response
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise HTTPException(status_code=500, detail="AI service unavailable")


# User Profile endpoints
@api_router.post("/profiles", response_model=UserProfile)
async def create_profile(profile_data: UserProfileCreate):
    profile_dict = profile_data.dict()
    profile = UserProfile(**profile_dict)
    await db.user_profiles.insert_one(profile.dict())
    return profile

@api_router.get("/profiles", response_model=List[UserProfile])
async def get_profiles():
    profiles = await db.user_profiles.find().to_list(1000)
    return [UserProfile(**profile) for profile in profiles]

@api_router.get("/profiles/{user_id}", response_model=UserProfile)
async def get_profile(user_id: str):
    profile = await db.user_profiles.find_one({"id": user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return UserProfile(**profile)

@api_router.put("/profiles/{user_id}", response_model=UserProfile)
async def update_profile(user_id: str, profile_data: UserProfileCreate):
    existing_profile = await db.user_profiles.find_one({"id": user_id})
    if not existing_profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    updated_data = profile_data.dict()
    updated_data["id"] = user_id
    updated_data["created_at"] = existing_profile["created_at"]

    updated_profile = UserProfile(**updated_data)
    await db.user_profiles.replace_one({"id": user_id}, updated_profile.dict())
    return updated_profile


# Job Analysis endpoints
@api_router.post("/analyze-job", response_model=JobAnalysisResult)
async def analyze_job(request: JobAnalysisRequest):
    # Get user profile
    profile = await db.user_profiles.find_one({"id": request.user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    user_profile = UserProfile(**profile)

    # Create system message for job analysis
    system_message = """You are an expert career advisor. Analyze job descriptions and provide detailed insights about:
1. Required qualifications (education, skills, experience)
2. Job responsibilities and requirements
3. Career level and growth potential
4. Salary expectations (if mentioned)
5. Company culture indicators
6. Match assessment for the given user profile

Respond in JSON format with the following structure:
{
    "required_education": "education level needed",
    "required_skills": ["skill1", "skill2"],
    "required_experience": "years of experience needed", 
    "responsibilities": ["responsibility1", "responsibility2"],
    "career_level": "entry/mid/senior level",
    "growth_potential": "description of growth opportunities",
    "salary_range": "salary information if available",
    "company_culture": "culture indicators",
    "match_assessment": "detailed assessment of user fit"
}"""

    # Create user message with job description and profile
    user_message = f"""
    Please analyze this job description:
    
    {request.job_description}
    
    For this user profile:
    - Name: {user_profile.name}
    - Education: {user_profile.education_level}
    - Field of Study: {user_profile.field_of_study}
    - Skills: {', '.join(user_profile.skills)}
    - Experience: {user_profile.experience_years} years
    - Current Role: {user_profile.current_role}
    - Career Interests: {', '.join(user_profile.career_interests)}
    """

    # Get AI analysis
    ai_response = await get_ai_response(system_message, user_message)

    # Parse AI response (assuming it returns JSON-like text)
    try:
        import json
        analysis = json.loads(ai_response)
    except:
        # If JSON parsing fails, create structured response
        analysis = {
            "analysis_text": ai_response,
            "parsed": False
        }

    # Generate recommendations based on analysis
    recommendations_prompt = f"""Based on the job analysis, provide 3-5 specific recommendations for the user to improve their candidacy for this role. Consider their current profile and what's missing."""

    recommendations_response = await get_ai_response(
        "You are a career coach providing actionable advice.",
        recommendations_prompt + f"\n\nJob Analysis: {ai_response}\n\nUser Profile: {user_message}"
    )

    # Calculate match score (simplified - you can enhance this)
    match_score = 0.75  # This would be calculated based on actual analysis

    # Save analysis result
    result = JobAnalysisResult(
        user_id=request.user_id,
        job_description=request.job_description,
        analysis=analysis,
        recommendations=recommendations_response.split('\n') if recommendations_response else [],
        match_score=match_score
    )

    await db.job_analyses.insert_one(result.dict())
    return result

@api_router.get("/job-analyses/{user_id}")
async def get_user_job_analyses(user_id: str):
    analyses = await db.job_analyses.find({"user_id": user_id}).to_list(100)
    return [JobAnalysisResult(**analysis) for analysis in analyses]


# Career Advice endpoints
@api_router.post("/career-advice", response_model=CareerAdviceResponse)
async def get_career_advice(request: CareerAdviceRequest):
    # Get user profile
    profile = await db.user_profiles.find_one({"id": request.user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    user_profile = UserProfile(**profile)

    # Create system message for career advice
    system_message = """You are an expert career advisor with deep knowledge of various industries, job markets, and career paths. Provide personalized, actionable career advice based on the user's profile and specific questions. Your advice should be:
1. Practical and actionable
2. Based on current job market trends
3. Tailored to their education and experience level
4. Encouraging yet realistic
5. Include specific next steps they can take"""

    # Create user message with query and profile context
    user_message = f"""
    User Question: {request.query}
    
    User Profile Context:
    - Name: {user_profile.name}
    - Education: {user_profile.education_level} in {user_profile.field_of_study}
    - Skills: {', '.join(user_profile.skills)}
    - Experience: {user_profile.experience_years} years
    - Current Role: {user_profile.current_role}
    - Career Interests: {', '.join(user_profile.career_interests)}
    
    Please provide detailed career advice addressing their question.
    """

    # Get AI advice
    advice = await get_ai_response(system_message, user_message)

    # Save advice
    advice_response = CareerAdviceResponse(
        user_id=request.user_id,
        query=request.query,
        advice=advice
    )

    await db.career_advice.insert_one(advice_response.dict())
    return advice_response

@api_router.get("/career-advice/{user_id}")
async def get_user_career_advice(user_id: str):
    advice_list = await db.career_advice.find({"user_id": user_id}).to_list(100)
    return [CareerAdviceResponse(**advice) for advice in advice_list]


# Market Insights endpoint
@api_router.get("/market-insights/{field}")
async def get_market_insights(field: str):
    system_message = """You are a job market analyst. Provide current insights about specific fields including:
1. Job market trends
2. In-demand skills
3. Salary ranges
4. Growth outlook
5. Top companies hiring
6. Emerging opportunities"""
    
    user_message = f"Provide comprehensive job market insights for the {field} field in 2025."
    
    insights = await get_ai_response(system_message, user_message)
    
    return {
        "field": field,
        "insights": insights,
        "generated_at": datetime.utcnow()
    }


# Anonymous Search Models
class AnonymousSearchRequest(BaseModel):
    query: str
    search_type: Optional[str] = "general"  # general, career_path, skills, industry

class AnonymousSearchResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    search_type: str
    response: str
    suggestions: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Anonymous Career Search endpoint
@api_router.post("/search", response_model=AnonymousSearchResponse)
async def anonymous_career_search(request: AnonymousSearchRequest):
    """
    Public search endpoint for anonymous users to get career guidance
    without creating a profile. Supports various search types.
    """
    
    # Define system messages based on search type
    system_messages = {
        "general": """You are an expert career advisor providing helpful, actionable career guidance. Answer career-related questions with:
1. Clear, practical advice
2. Current industry insights
3. Specific next steps
4. Educational requirements when relevant
5. Growth opportunities
Keep responses comprehensive but concise.""",
        
        "career_path": """You are a career path specialist. Help users understand different career trajectories by providing:
1. Various career options in their area of interest
2. Educational requirements for each path
3. Typical career progression
4. Skills needed at each level
5. Salary expectations
6. Industry outlook""",
        
        "skills": """You are a skills development advisor. Focus on:
1. Current in-demand skills in the relevant field
2. How to develop these skills (courses, certifications, practice)
3. Skill progression pathways
4. Time investment needed
5. Best resources for learning
6. How skills translate to job opportunities""",
        
        "industry": """You are an industry analyst. Provide insights about:
1. Industry trends and growth
2. Major companies and employers
3. Geographic job markets
4. Salary ranges and compensation
5. Future outlook and opportunities
6. Entry points into the industry""",
        
        "academic_pathways": """You are an academic and career counselor specializing in connecting degree programs to career opportunities. Provide comprehensive guidance about:
1. Specific degree programs that lead to mentioned job titles/careers
2. Alternative academic pathways (different degrees that can lead to the same career)
3. Required coursework and key subjects to focus on
4. Additional certifications or skills needed beyond the degree
5. Internship and co-op opportunities relevant to the field
6. Graduate school considerations (when advanced degrees are beneficial)
7. Timeline from degree completion to career entry
8. Skills gap analysis - what students should learn beyond their degree curriculum
9. University program rankings and recommendations when relevant
10. Career progression paths for degree holders

Focus especially on helping university students understand how their academic choices connect to real-world career opportunities."""
    }
    
    system_message = system_messages.get(request.search_type, system_messages["general"])
    
    # Enhanced user message with context
    user_message = f"""
    User Query: {request.query}
    
    Please provide comprehensive career guidance addressing this question. If the query is broad, break down your response into actionable sections and provide specific guidance they can follow.
    """
    
    # Get AI response
    response = await get_ai_response(system_message, user_message)
    
    # Generate related suggestions based on the query
    suggestions_prompt = f"""Based on this career query: "{request.query}", suggest 3-4 related questions or topics the user might want to explore next. Return only the suggestions, one per line."""
    
    suggestions_response = await get_ai_response(
        "You are a career advisor helping users discover related topics of interest.",
        suggestions_prompt
    )
    
    # Parse suggestions
    suggestions = [s.strip() for s in suggestions_response.split('\n') if s.strip() and not s.strip().startswith('-')][:4]
    if not suggestions:
        suggestions = [
            "What skills are most in-demand in this field?",
            "What are the typical career paths?",
            "What education is required?",
            "What's the job market outlook?"
        ]
    
    # Save search for analytics (optional)
    search_response = AnonymousSearchResponse(
        query=request.query,
        search_type=request.search_type,
        response=response,
        suggestions=suggestions
    )
    
    # Optionally save to database for analytics
    try:
        await db.anonymous_searches.insert_one(search_response.dict())
    except Exception as e:
        logger.warning(f"Failed to save anonymous search: {e}")
    
    return search_response


# Popular Career Topics endpoint
@api_router.get("/popular-topics")
async def get_popular_topics():
    """Get popular career topics and trending searches"""
    
    # You could make this dynamic by analyzing search history
    # For now, return curated popular topics
    topics = {
        "trending_careers": [
            "AI/Machine Learning Engineer",
            "Data Scientist",
            "Cybersecurity Specialist",
            "Product Manager",
            "UX/UI Designer",
            "Cloud Engineer",
            "Digital Marketing Specialist",
            "Software Developer"
        ],
        "popular_questions": [
            "How to break into tech without a CS degree?",
            "What skills do I need for data science?",
            "How to transition careers at 30+?",
            "Remote work opportunities in marketing",
            "What careers can I pursue with a psychology degree?",
            "Which degree is best for product management?",
            "How to negotiate salary?",
            "Best certifications for career growth"
        ],
        "industry_insights": [
            "Technology",
            "Healthcare",
            "Finance",
            "Education",
            "Manufacturing",
            "Renewable Energy",
            "E-commerce",
            "Biotechnology"
        ]
    }
    
    return topics

# Degree Programs to Career Mapping endpoint
@api_router.get("/degree-programs")
async def get_degree_programs():
    """Get comprehensive mapping of degree programs to career opportunities"""
    
    degree_mappings = {
        "stem_fields": {
            "Computer Science": {
                "direct_careers": [
                    "Software Developer/Engineer",
                    "Data Scientist",
                    "AI/Machine Learning Engineer",
                    "Cybersecurity Specialist",
                    "DevOps Engineer",
                    "Product Manager (Technical)",
                    "Research Scientist"
                ],
                "alternative_paths": [
                    "Digital Marketing Specialist",
                    "Technical Writer",
                    "IT Consultant",
                    "Startup Founder",
                    "Technical Sales Engineer"
                ],
                "skills_gap": [
                    "Industry-specific domain knowledge",
                    "Soft skills and communication",
                    "Project management",
                    "Cloud platforms proficiency",
                    "Advanced system design"
                ]
            },
            "Data Science/Statistics": {
                "direct_careers": [
                    "Data Scientist",
                    "Data Analyst",
                    "Business Intelligence Analyst",
                    "Research Analyst",
                    "Quantitative Analyst",
                    "Machine Learning Engineer"
                ],
                "alternative_paths": [
                    "Product Manager",
                    "Management Consultant",
                    "Risk Analyst",
                    "Marketing Analyst",
                    "Operations Research Analyst"
                ],
                "skills_gap": [
                    "Domain expertise in target industry",
                    "Advanced programming skills",
                    "Big data technologies",
                    "Data visualization tools",
                    "Business communication skills"
                ]
            },
            "Engineering (General)": {
                "direct_careers": [
                    "Design Engineer",
                    "Project Engineer",
                    "Systems Engineer",
                    "Quality Engineer",
                    "Manufacturing Engineer",
                    "Research & Development Engineer"
                ],
                "alternative_paths": [
                    "Technical Product Manager",
                    "Engineering Consultant",
                    "Patent Attorney",
                    "Technical Sales",
                    "Startup Founder"
                ],
                "skills_gap": [
                    "Industry certifications",
                    "Project management",
                    "Modern software tools",
                    "Business acumen",
                    "Leadership skills"
                ]
            }
        },
        "business_fields": {
            "Business Administration/Management": {
                "direct_careers": [
                    "Business Analyst",
                    "Project Manager",
                    "Operations Manager",
                    "HR Manager",
                    "Marketing Manager",
                    "Financial Analyst"
                ],
                "alternative_paths": [
                    "Management Consultant",
                    "Product Manager",
                    "Entrepreneur",
                    "Sales Manager",
                    "Business Development"
                ],
                "skills_gap": [
                    "Industry-specific knowledge",
                    "Advanced analytics",
                    "Digital marketing",
                    "Data analysis tools",
                    "Technical literacy"
                ]
            },
            "Economics": {
                "direct_careers": [
                    "Economic Analyst",
                    "Financial Analyst",
                    "Policy Analyst",
                    "Research Economist",
                    "Market Research Analyst"
                ],
                "alternative_paths": [
                    "Data Scientist",
                    "Investment Banking",
                    "Management Consultant",
                    "Business Development",
                    "Government Positions"
                ],
                "skills_gap": [
                    "Programming (Python/R)",
                    "Advanced statistical software",
                    "Database management",
                    "Financial modeling",
                    "Industry regulations"
                ]
            },
            "Marketing": {
                "direct_careers": [
                    "Digital Marketing Specialist",
                    "Brand Manager",
                    "Content Marketing Manager",
                    "Social Media Manager",
                    "Marketing Analyst"
                ],
                "alternative_paths": [
                    "Product Manager",
                    "UX Researcher",
                    "Business Development",
                    "Sales Manager",
                    "PR Specialist"
                ],
                "skills_gap": [
                    "Data analytics and metrics",
                    "Marketing automation tools",
                    "SEO/SEM expertise",
                    "A/B testing",
                    "Customer psychology"
                ]
            }
        },
        "liberal_arts": {
            "Psychology": {
                "direct_careers": [
                    "Clinical Psychologist",
                    "Counseling Psychologist",
                    "UX Researcher",
                    "HR Specialist",
                    "Market Research Analyst"
                ],
                "alternative_paths": [
                    "Product Manager",
                    "Data Analyst",
                    "Social Media Manager",
                    "Training Coordinator",
                    "Sales Representative"
                ],
                "skills_gap": [
                    "Research methodology",
                    "Statistical analysis software",
                    "Business knowledge",
                    "Technology tools",
                    "Industry certifications"
                ]
            },
            "Communication": {
                "direct_careers": [
                    "Public Relations Specialist",
                    "Content Writer",
                    "Digital Marketing Manager",
                    "Social Media Manager",
                    "Corporate Communications"
                ],
                "alternative_paths": [
                    "UX Writer",
                    "Product Marketing Manager",
                    "Training Specialist",
                    "Event Coordinator",
                    "Business Analyst"
                ],
                "skills_gap": [
                    "Digital marketing tools",
                    "Data analysis",
                    "SEO knowledge",
                    "Design basics",
                    "Project management"
                ]
            }
        },
        "healthcare_fields": {
            "Biology/Biomedical Sciences": {
                "direct_careers": [
                    "Research Scientist",
                    "Laboratory Technician",
                    "Quality Control Analyst",
                    "Biomedical Engineer",
                    "Clinical Research Coordinator"
                ],
                "alternative_paths": [
                    "Pharmaceutical Sales",
                    "Science Writer",
                    "Patent Analyst",
                    "Regulatory Affairs",
                    "Biotech Consultant"
                ],
                "skills_gap": [
                    "Regulatory knowledge",
                    "Business skills",
                    "Advanced instrumentation",
                    "Data analysis",
                    "Project management"
                ]
            }
        }
    }
    
    return degree_mappings


# Enhanced Degree-Career Search endpoint
@api_router.post("/degree-career-search")
async def degree_career_search(request: dict):
    """
    AI-powered search specifically for connecting degrees to careers
    """
    degree = request.get('degree', '')
    career_interest = request.get('career_interest', '')
    
    system_message = """You are a specialized academic and career counselor. Help students understand the connection between their degree program and career opportunities. Provide:

1. **Direct Career Paths**: Jobs directly related to the degree
2. **Alternative Career Paths**: Unexpected but viable career options
3. **Skills Development**: What skills to develop beyond coursework
4. **Education Enhancement**: Additional certifications, minors, or courses to consider
5. **Timeline**: Realistic timeline from graduation to career establishment
6. **Success Stories**: Examples of graduates who succeeded in various paths
7. **Action Steps**: Specific next steps the student can take now

Make your response practical, encouraging, and actionable."""
    
    user_message = f"""
    Student's Degree Program: {degree}
    Career Interest/Area: {career_interest}
    
    Please provide comprehensive guidance on how this degree can lead to career success, including both traditional and non-traditional paths.
    """
    
    response = await get_ai_response(system_message, user_message)
    
    return {
        "degree": degree,
        "career_interest": career_interest,
        "guidance": response,
        "generated_at": datetime.utcnow().isoformat()
    }


# ====================================
# NEXTSTEP JOB ADVISORY ENDPOINTS
# ====================================

# Job Scraping and Processing
@api_router.post("/jobs/scrape")
async def scrape_jobs(request: JobSearchRequest, background_tasks: BackgroundTasks):
    """
    Scrape jobs from multiple sources and process them
    """
    try:
        all_scraped_jobs = []
        
        # Scrape from selected sources
        for source_name in request.sources:
            if source_name not in scrapers:
                continue
                
            scraper = scrapers[source_name]
            
            try:
                async with scraper:
                    jobs = await scraper.scrape_job_listings(
                        search_terms=request.search_terms,
                        location=request.location,
                        limit=request.limit_per_source
                    )
                    all_scraped_jobs.extend(jobs)
                    
            except Exception as e:
                logger.error(f"Error scraping from {source_name}: {e}")
                continue
        
        # Store initial job records (title + link only)
        stored_count = 0
        for job in all_scraped_jobs:
            try:
                await db.raw_jobs.insert_one(job)
                stored_count += 1
            except Exception as e:
                logger.warning(f"Error storing job {job.get('id')}: {e}")
        
        # Process jobs in background
        background_tasks.add_task(process_scraped_jobs, [job['id'] for job in all_scraped_jobs])
        
        return {
            "status": "success",
            "message": f"Scraped {len(all_scraped_jobs)} jobs from {len(request.sources)} sources",
            "jobs_stored": stored_count,
            "processing_started": True,
            "sources_used": request.sources
        }
        
    except Exception as e:
        logger.error(f"Error in job scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_scraped_jobs(job_ids: List[str]):
    """
    Background task to process scraped jobs through pipeline
    """
    try:
        # Fetch raw jobs
        raw_jobs = []
        async for job in db.raw_jobs.find({"id": {"$in": job_ids}}):
            raw_jobs.append(job)
        
        # Process through pipeline
        processed_jobs = await process_job_batch(raw_jobs, batch_size=3)
        
        # Store processed jobs
        for processed_job in processed_jobs:
            try:
                await db.processed_jobs.replace_one(
                    {"id": processed_job["id"]}, 
                    processed_job, 
                    upsert=True
                )
            except Exception as e:
                logger.error(f"Error storing processed job: {e}")
                
        logger.info(f"Successfully processed {len(processed_jobs)} jobs")
        
    except Exception as e:
        logger.error(f"Error in background job processing: {e}")

# Job Search and Filtering
@api_router.post("/jobs/search")
async def search_jobs(filters: JobFilterRequest, skip: int = 0, limit: int = 20):
    """
    Search and filter processed jobs
    """
    try:
        # Build query
        query = {"processed": True}
        
        if filters.industry:
            query["$or"] = [
                {"industry": {"$regex": filters.industry, "$options": "i"}},
                {"ai_industry_category": {"$regex": filters.industry, "$options": "i"}}
            ]
            
        if filters.job_type:
            query["job_type"] = {"$regex": filters.job_type, "$options": "i"}
            
        if filters.experience_level:
            query["$or"] = [
                {"experience_level": {"$regex": filters.experience_level, "$options": "i"}},
                {"ai_role_level": {"$regex": filters.experience_level, "$options": "i"}}
            ]
            
        if filters.location:
            query["location"] = {"$regex": filters.location, "$options": "i"}
            
        if filters.company:
            query["company"] = {"$regex": filters.company, "$options": "i"}
            
        if filters.remote_friendly is not None:
            query["remote_friendly"] = filters.remote_friendly
            
        if filters.skills:
            query["$or"] = [
                {"skills": {"$in": filters.skills}},
                {"ai_skills_analysis": {"$in": filters.skills}}
            ]
            
        if filters.posted_days_ago:
            cutoff_date = datetime.utcnow() - timedelta(days=filters.posted_days_ago)
            query["scraped_at"] = {"$gte": cutoff_date}
            
        # Salary filtering (if salary data exists)
        salary_query = []
        if filters.salary_min:
            salary_query.append({
                "$or": [
                    {"salary.min": {"$gte": filters.salary_min}},
                    {"salary.amount": {"$gte": filters.salary_min}}
                ]
            })
        if filters.salary_max:
            salary_query.append({
                "$or": [
                    {"salary.max": {"$lte": filters.salary_max}},
                    {"salary.amount": {"$lte": filters.salary_max}}
                ]
            })
        if salary_query:
            query["$and"] = query.get("$and", []) + salary_query
        
        # Execute search
        total_count = await db.processed_jobs.count_documents(query)
        
        jobs_cursor = db.processed_jobs.find(query).sort("quality_score", -1).skip(skip).limit(limit)
        jobs = []
        async for job in jobs_cursor:
            job["_id"] = str(job["_id"])  # Convert ObjectId to string
            jobs.append(job)
        
        return {
            "jobs": jobs,
            "total": total_count,
            "page": skip // limit + 1,
            "pages": (total_count + limit - 1) // limit,
            "filters_applied": filters.dict(exclude_none=True)
        }
        
    except Exception as e:
        logger.error(f"Error searching jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Job Recommendations
@api_router.post("/jobs/recommendations/{user_id}")
async def get_job_recommendations(user_id: str, limit: int = 10):
    """
    Get personalized job recommendations for a user
    """
    try:
        # Get user profile
        user = await db.profiles.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Build recommendation query based on user profile
        user_skills = set(skill.lower() for skill in user.get("skills", []))
        user_interests = set(interest.lower() for interest in user.get("career_interests", []))
        user_locations = user.get("preferred_locations", [])
        user_experience = user.get("experience_years", 0)
        
        def get_experience_level(years: int) -> str:
            if years == 0:
                return "Entry Level"
            elif years <= 2:
                return "Junior"
            elif years <= 5:
                return "Mid Level"
            elif years <= 8:
                return "Senior"
            else:
                return "Expert"
                
        def get_adjacent_experience_levels(years: int) -> List[str]:
            current = get_experience_level(years)
            levels = ["Entry Level", "Junior", "Mid Level", "Senior", "Expert"]
            try:
                idx = levels.index(current)
                adjacent = []
                if idx > 0:
                    adjacent.append(levels[idx - 1])
                if idx < len(levels) - 1:
                    adjacent.append(levels[idx + 1])
                return adjacent
            except ValueError:
                return []
        
        # Create recommendation pipeline
        pipeline = [
            {"$match": {"processed": True, "quality_score": {"$gte": 0.5}}},
            {
                "$addFields": {
                    "recommendation_score": {
                        "$add": [
                            # Skill matching score (0-40 points)
                            {
                                "$multiply": [
                                    {
                                        "$size": {
                                            "$setIntersection": [
                                                {"$map": {"input": "$skills", "as": "skill", "in": {"$toLower": "$$skill"}}},
                                                list(user_skills)
                                            ]
                                        }
                                    },
                                    8  # 8 points per matching skill
                                ]
                            },
                            # Interest matching score (0-30 points)
                            {
                                "$cond": [
                                    {
                                        "$gt": [
                                            {
                                                "$size": {
                                                    "$setIntersection": [
                                                        {"$map": {"input": "$career_interests", "as": "interest", "in": {"$toLower": "$$interest"}}},
                                                        list(user_interests)
                                                    ]
                                                }
                                            },
                                            0
                                        ]
                                    },
                                    30,
                                    0
                                ]
                            },
                            # Experience level matching (0-20 points)
                            {
                                "$cond": [
                                    {"$eq": ["$ai_role_level", get_experience_level(user_experience)]},
                                    20,
                                    {
                                        "$cond": [
                                            {"$in": ["$ai_role_level", get_adjacent_experience_levels(user_experience)]},
                                            10,
                                            0
                                        ]
                                    }
                                ]
                            },
                            # Location preference (0-10 points)
                            {
                                "$cond": [
                                    {"$in": ["$location", user_locations]} if user_locations else False,
                                    10,
                                    0
                                ]
                            }
                        ]
                    }
                }
            },
            {"$sort": {"recommendation_score": -1, "quality_score": -1}},
            {"$limit": limit}
        ]
        
        recommendations = []
        async for job in db.processed_jobs.aggregate(pipeline):
            job["_id"] = str(job["_id"])
            recommendations.append(job)
        
        return {
            "recommendations": recommendations,
            "user_id": user_id,
            "recommendation_criteria": {
                "skills_matched": list(user_skills),
                "interests": list(user_interests),
                "experience_level": get_experience_level(user_experience),
                "preferred_locations": user_locations
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Job Market Analysis
@api_router.post("/market/analysis")
async def analyze_job_market(request: MarketAnalysisRequest):
    """
    Analyze job market trends and insights
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=request.time_period)
        base_query = {"processed": True, "scraped_at": {"$gte": cutoff_date}}
        
        # Apply filters
        if request.industry:
            base_query["$or"] = [
                {"industry": {"$regex": request.industry, "$options": "i"}},
                {"ai_industry_category": {"$regex": request.industry, "$options": "i"}}
            ]
        if request.location:
            base_query["location"] = {"$regex": request.location, "$options": "i"}
        if request.job_title:
            base_query["title"] = {"$regex": request.job_title, "$options": "i"}
        
        # Industry distribution
        industry_pipeline = [
            {"$match": base_query},
            {"$group": {"_id": "$industry", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        # Salary analysis
        salary_pipeline = [
            {"$match": {**base_query, "salary": {"$exists": True, "$ne": None}}},
            {
                "$group": {
                    "_id": None,
                    "avg_salary": {"$avg": {"$ifNull": ["$salary.amount", {"$avg": ["$salary.min", "$salary.max"]}]}},
                    "min_salary": {"$min": {"$ifNull": ["$salary.amount", "$salary.min"]}},
                    "max_salary": {"$max": {"$ifNull": ["$salary.amount", "$salary.max"]}},
                    "count": {"$sum": 1}
                }
            }
        ]
        
        # Top skills
        skills_pipeline = [
            {"$match": base_query},
            {"$unwind": "$skills"},
            {"$group": {"_id": "$skills", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 15}
        ]
        
        # Experience level distribution
        experience_pipeline = [
            {"$match": base_query},
            {"$group": {"_id": "$experience_level", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        # Company analysis
        company_pipeline = [
            {"$match": base_query},
            {"$group": {"_id": "$company", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        # Execute all pipelines
        industry_data = [doc async for doc in db.processed_jobs.aggregate(industry_pipeline)]
        salary_data = [doc async for doc in db.processed_jobs.aggregate(salary_pipeline)]
        skills_data = [doc async for doc in db.processed_jobs.aggregate(skills_pipeline)]
        experience_data = [doc async for doc in db.processed_jobs.aggregate(experience_pipeline)]
        company_data = [doc async for doc in db.processed_jobs.aggregate(company_pipeline)]
        
        # Total jobs count
        total_jobs = await db.processed_jobs.count_documents(base_query)
        
        return {
            "analysis_period": f"Last {request.time_period} days",
            "total_jobs_analyzed": total_jobs,
            "industry_distribution": industry_data,
            "salary_insights": salary_data[0] if salary_data else None,
            "top_skills": skills_data,
            "experience_distribution": experience_data,
            "top_companies": company_data,
            "market_trends": await generate_market_insights(request, total_jobs),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in market analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Skills Gap Analysis
@api_router.post("/analysis/skills-gap/{user_id}")
async def analyze_skills_gap(user_id: str, target_roles: List[str]):
    """
    Analyze skills gap between user profile and target roles
    """
    try:
        # Get user profile
        user = await db.profiles.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        user_skills = set(skill.lower() for skill in user.get("skills", []))
        
        # Analyze target roles
        role_analysis = []
        for role in target_roles:
            # Find jobs matching this role
            role_query = {"processed": True, "title": {"$regex": role, "$options": "i"}}
            
            # Get skills required for this role
            skills_pipeline = [
                {"$match": role_query},
                {"$unwind": "$skills"},
                {"$group": {"_id": "$skills", "frequency": {"$sum": 1}}},
                {"$sort": {"frequency": -1}},
                {"$limit": 20}
            ]
            
            role_skills = []
            async for skill_doc in db.processed_jobs.aggregate(skills_pipeline):
                role_skills.append({
                    "skill": skill_doc["_id"],
                    "frequency": skill_doc["frequency"],
                    "user_has": skill_doc["_id"].lower() in user_skills
                })
            
            # Calculate gap
            total_skills = len(role_skills)
            user_has_skills = sum(1 for skill in role_skills if skill["user_has"])
            gap_percentage = ((total_skills - user_has_skills) / total_skills * 100) if total_skills > 0 else 0
            
            missing_skills = [skill["skill"] for skill in role_skills if not skill["user_has"]][:10]
            
            role_analysis.append({
                "role": role,
                "skills_analysis": role_skills,
                "gap_percentage": round(gap_percentage, 2),
                "missing_skills": missing_skills,
                "matching_skills": user_has_skills,
                "total_skills_required": total_skills
            })
        
        # Generate recommendations
        recommendations = await generate_skills_recommendations(user, role_analysis)
        
        return {
            "user_id": user_id,
            "current_skills": list(user_skills),
            "target_roles_analysis": role_analysis,
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in skills gap analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Saved Jobs Management
@api_router.post("/jobs/save")
async def save_job(saved_job: SavedJob):
    """Save a job to user's collection"""
    try:
        # Check if job exists
        job = await db.processed_jobs.find_one({"id": saved_job.job_id})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if already saved
        existing = await db.saved_jobs.find_one({
            "user_id": saved_job.user_id,
            "job_id": saved_job.job_id
        })
        
        if existing:
            # Update existing
            await db.saved_jobs.update_one(
                {"_id": existing["_id"]},
                {"$set": saved_job.dict()}
            )
            return {"message": "Job updated in saved collection"}
        else:
            # Create new
            await db.saved_jobs.insert_one(saved_job.dict())
            return {"message": "Job saved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/jobs/saved/{user_id}")
async def get_saved_jobs(user_id: str):
    """Get user's saved jobs"""
    try:
        saved_jobs = []
        async for saved_job in db.saved_jobs.find({"user_id": user_id}):
            # Get job details
            job = await db.processed_jobs.find_one({"id": saved_job["job_id"]})
            if job:
                saved_job["job_details"] = job
                saved_job["_id"] = str(saved_job["_id"])
                saved_jobs.append(saved_job)
        
        return {"saved_jobs": saved_jobs}
        
    except Exception as e:
        logger.error(f"Error fetching saved jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Job Alerts
@api_router.post("/alerts/create")
async def create_job_alert(alert: JobAlert):
    """Create a job alert for user"""
    try:
        await db.job_alerts.insert_one(alert.dict())
        return {"message": "Job alert created successfully", "alert_id": alert.id}
    except Exception as e:
        logger.error(f"Error creating job alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/alerts/{user_id}")
async def get_job_alerts(user_id: str):
    """Get user's job alerts"""
    try:
        alerts = []
        async for alert in db.job_alerts.find({"user_id": user_id}):
            alert["_id"] = str(alert["_id"])
            alerts.append(alert)
        return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Error fetching job alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
async def generate_market_insights(request: MarketAnalysisRequest, total_jobs: int) -> str:
    """Generate AI-powered market insights"""
    try:
        prompt = f"""
        Analyze the job market data for the following criteria:
        - Industry: {request.industry or 'All industries'}
        - Location: {request.location or 'All locations'}
        - Job Title: {request.job_title or 'All positions'}
        - Time Period: Last {request.time_period} days
        - Total Jobs Analyzed: {total_jobs}
        
        Provide key insights about:
        1. Market demand trends
        2. Growth opportunities
        3. Salary expectations
        4. Skills in demand
        5. Career advice for professionals in this area
        
        Keep response concise but informative (max 300 words).
        """
        
        response = await get_ai_response(
            "You are a job market analyst providing insights based on data.",
            prompt
        )
        return response
    except Exception as e:
        logger.error(f"Error generating market insights: {e}")
        return "Market insights temporarily unavailable"

async def generate_skills_recommendations(user: Dict, role_analysis: List[Dict]) -> List[str]:
    """Generate personalized skills recommendations"""
    try:
        # Collect all missing skills across target roles
        all_missing_skills = []
        for analysis in role_analysis:
            all_missing_skills.extend(analysis["missing_skills"])
        
        # Count frequency of missing skills
        skill_frequency = {}
        for skill in all_missing_skills:
            skill_frequency[skill] = skill_frequency.get(skill, 0) + 1
        
        # Get top missing skills
        top_missing = sorted(skill_frequency.items(), key=lambda x: x[1], reverse=True)[:8]
        
        recommendations = []
        for skill, frequency in top_missing:
            recommendations.append(f"Learn {skill} (required in {frequency} target roles)")
        
        return recommendations
    except Exception as e:
        logger.error(f"Error generating skills recommendations: {e}")
        return ["Skills analysis temporarily unavailable"]

# Add basic endpoints
@api_router.get("/")
async def root():
    return {"message": "Career Advisor API - Empowering your career journey with AI"}

# Define Models
class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    education_level: str  # High School, Bachelor's, Master's, PhD, etc.
    field_of_study: Optional[str] = None
    skills: List[str] = []
    experience_years: int = 0
    current_role: Optional[str] = None
    career_interests: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserProfileCreate(BaseModel):
    name: str
    education_level: str
    field_of_study: Optional[str] = None
    skills: List[str] = []
    experience_years: int = 0
    current_role: Optional[str] = None
    career_interests: List[str] = []

class JobAnalysisRequest(BaseModel):
    user_id: str
    job_description: str

class JobAnalysisResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    job_description: str
    analysis: Dict[str, Any]
    recommendations: List[str]
    match_score: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CareerAdviceRequest(BaseModel):
    user_id: str
    query: str

class CareerAdviceResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    query: str
    advice: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Helper function to get OpenAI response
async def get_ai_response(system_message: str, user_message: str) -> str:
    try:
        chat = LlmChat(
            api_key=os.environ.get('OPENAI_API_KEY'),
            session_id=str(uuid.uuid4()),
            system_message=system_message
        ).with_model("openai", "gpt-4o")
        
        message = UserMessage(text=user_message)
        response = await chat.send_message(message)
        return response
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise HTTPException(status_code=500, detail="AI service unavailable")


# User Profile endpoints
@api_router.post("/profiles", response_model=UserProfile)
async def create_profile(profile_data: UserProfileCreate):
    profile_dict = profile_data.dict()
    profile = UserProfile(**profile_dict)
    await db.user_profiles.insert_one(profile.dict())
    return profile

@api_router.get("/profiles", response_model=List[UserProfile])
async def get_profiles():
    profiles = await db.user_profiles.find().to_list(1000)
    return [UserProfile(**profile) for profile in profiles]

@api_router.get("/profiles/{user_id}", response_model=UserProfile)
async def get_profile(user_id: str):
    profile = await db.user_profiles.find_one({"id": user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return UserProfile(**profile)

@api_router.put("/profiles/{user_id}", response_model=UserProfile)
async def update_profile(user_id: str, profile_data: UserProfileCreate):
    existing_profile = await db.user_profiles.find_one({"id": user_id})
    if not existing_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    updated_data = profile_data.dict()
    updated_data["id"] = user_id
    updated_data["created_at"] = existing_profile["created_at"]
    
    updated_profile = UserProfile(**updated_data)
    await db.user_profiles.replace_one({"id": user_id}, updated_profile.dict())
    return updated_profile


# Job Analysis endpoints
@api_router.post("/analyze-job", response_model=JobAnalysisResult)
async def analyze_job(request: JobAnalysisRequest):
    # Get user profile
    profile = await db.user_profiles.find_one({"id": request.user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    user_profile = UserProfile(**profile)
    
    # Create system message for job analysis
    system_message = """You are an expert career advisor. Analyze job descriptions and provide detailed insights about:
1. Required qualifications (education, skills, experience)
2. Job responsibilities and requirements
3. Career level and growth potential
4. Salary expectations (if mentioned)
5. Company culture indicators
6. Match assessment for the given user profile

Respond in JSON format with the following structure:
{
    "required_education": "education level needed",
    "required_skills": ["skill1", "skill2"],
    "required_experience": "years of experience needed", 
    "responsibilities": ["responsibility1", "responsibility2"],
    "career_level": "entry/mid/senior level",
    "growth_potential": "description of growth opportunities",
    "salary_range": "salary information if available",
    "company_culture": "culture indicators",
    "match_assessment": "detailed assessment of user fit"
}"""
    
    # Create user message with job description and profile
    user_message = f"""
    Please analyze this job description:
    
    {request.job_description}
    
    For this user profile:
    - Name: {user_profile.name}
    - Education: {user_profile.education_level}
    - Field of Study: {user_profile.field_of_study}
    - Skills: {', '.join(user_profile.skills)}
    - Experience: {user_profile.experience_years} years
    - Current Role: {user_profile.current_role}
    - Career Interests: {', '.join(user_profile.career_interests)}
    """
    
    # Get AI analysis
    ai_response = await get_ai_response(system_message, user_message)
    
    # Parse AI response (assuming it returns JSON-like text)
    try:
        import json
        analysis = json.loads(ai_response)
    except:
        # If JSON parsing fails, create structured response
        analysis = {
            "analysis_text": ai_response,
            "parsed": False
        }
    
    # Generate recommendations based on analysis
    recommendations_prompt = f"""Based on the job analysis, provide 3-5 specific recommendations for the user to improve their candidacy for this role. Consider their current profile and what's missing."""
    
    recommendations_response = await get_ai_response(
        "You are a career coach providing actionable advice.",
        recommendations_prompt + f"\n\nJob Analysis: {ai_response}\n\nUser Profile: {user_message}"
    )
    
    # Calculate match score (simplified - you can enhance this)
    match_score = 0.75  # This would be calculated based on actual analysis
    
    # Save analysis result
    result = JobAnalysisResult(
        user_id=request.user_id,
        job_description=request.job_description,
        analysis=analysis,
        recommendations=recommendations_response.split('\n') if recommendations_response else [],
        match_score=match_score
    )
    
    await db.job_analyses.insert_one(result.dict())
    return result

@api_router.get("/job-analyses/{user_id}")
async def get_user_job_analyses(user_id: str):
    analyses = await db.job_analyses.find({"user_id": user_id}).to_list(100)
    return [JobAnalysisResult(**analysis) for analysis in analyses]


# Career Advice endpoints
@api_router.post("/career-advice", response_model=CareerAdviceResponse)
async def get_career_advice(request: CareerAdviceRequest):
    # Get user profile
    profile = await db.user_profiles.find_one({"id": request.user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    user_profile = UserProfile(**profile)
    
    # Create system message for career advice
    system_message = """You are an expert career advisor with deep knowledge of various industries, job markets, and career paths. Provide personalized, actionable career advice based on the user's profile and specific questions. Your advice should be:
1. Practical and actionable
2. Based on current job market trends
3. Tailored to their education and experience level
4. Encouraging yet realistic
5. Include specific next steps they can take"""
    
    # Create user message with query and profile context
    user_message = f"""
    User Question: {request.query}
    
    User Profile Context:
    - Name: {user_profile.name}
    - Education: {user_profile.education_level} in {user_profile.field_of_study}
    - Skills: {', '.join(user_profile.skills)}
    - Experience: {user_profile.experience_years} years
    - Current Role: {user_profile.current_role}
    - Career Interests: {', '.join(user_profile.career_interests)}
    
    Please provide detailed career advice addressing their question.
    """
    
    # Get AI advice
    advice = await get_ai_response(system_message, user_message)
    
    # Save advice
    advice_response = CareerAdviceResponse(
        user_id=request.user_id,
        query=request.query,
        advice=advice
    )
    
    await db.career_advice.insert_one(advice_response.dict())
    return advice_response

@api_router.get("/career-advice/{user_id}")
async def get_user_career_advice(user_id: str):
    advice_list = await db.career_advice.find({"user_id": user_id}).to_list(100)
    return [CareerAdviceResponse(**advice) for advice in advice_list]


# Market Insights endpoint
@api_router.get("/market-insights/{field}")
async def get_market_insights(field: str):
    system_message = """You are a job market analyst. Provide current insights about specific fields including:
1. Job market trends
2. In-demand skills
3. Salary ranges
4. Growth outlook
5. Top companies hiring
6. Emerging opportunities"""
    
    user_message = f"Provide comprehensive job market insights for the {field} field in 2025."
    
    insights = await get_ai_response(system_message, user_message)
    
    return {
        "field": field,
        "insights": insights,
        "generated_at": datetime.utcnow()
    }


# Anonymous Search Models
class AnonymousSearchRequest(BaseModel):
    query: str
    search_type: Optional[str] = "general"  # general, career_path, skills, industry

class AnonymousSearchResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    search_type: str
    response: str
    suggestions: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Anonymous Career Search endpoint
@api_router.post("/search", response_model=AnonymousSearchResponse)
async def anonymous_career_search(request: AnonymousSearchRequest):
    """
    Public search endpoint for anonymous users to get career guidance
    without creating a profile. Supports various search types.
    """
    
    # Define system messages based on search type
    system_messages = {
        "general": """You are an expert career advisor providing helpful, actionable career guidance. Answer career-related questions with:
1. Clear, practical advice
2. Current industry insights
3. Specific next steps
4. Educational requirements when relevant
5. Growth opportunities
Keep responses comprehensive but concise.""",
        
        "career_path": """You are a career path specialist. Help users understand different career trajectories by providing:
1. Various career options in their area of interest
2. Educational requirements for each path
3. Typical career progression
4. Skills needed at each level
5. Salary expectations
6. Industry outlook""",
        
        "skills": """You are a skills development advisor. Focus on:
1. Current in-demand skills in the relevant field
2. How to develop these skills (courses, certifications, practice)
3. Skill progression pathways
4. Time investment needed
5. Best resources for learning
6. How skills translate to job opportunities""",
        
        "industry": """You are an industry analyst. Provide insights about:
1. Industry trends and growth
2. Major companies and employers
3. Geographic job markets
4. Salary ranges and compensation
5. Future outlook and opportunities
6. Entry points into the industry"""
    }
    
    system_message = system_messages.get(request.search_type, system_messages["general"])
    
    # Enhanced user message with context
    user_message = f"""
    User Query: {request.query}
    
    Please provide comprehensive career guidance addressing this question. If the query is broad, break down your response into actionable sections and provide specific guidance they can follow.
    """
    
    # Get AI response
    response = await get_ai_response(system_message, user_message)
    
    # Generate related suggestions based on the query
    suggestions_prompt = f"""Based on this career query: "{request.query}", suggest 3-4 related questions or topics the user might want to explore next. Return only the suggestions, one per line."""
    
    suggestions_response = await get_ai_response(
        "You are a career advisor helping users discover related topics of interest.",
        suggestions_prompt
    )
    
    # Parse suggestions
    suggestions = [s.strip() for s in suggestions_response.split('\n') if s.strip() and not s.strip().startswith('-')][:4]
    if not suggestions:
        suggestions = [
            "What skills are most in-demand in this field?",
            "What are the typical career paths?",
            "What education is required?",
            "What's the job market outlook?"
        ]
    
    # Save search for analytics (optional)
    search_response = AnonymousSearchResponse(
        query=request.query,
        search_type=request.search_type,
        response=response,
        suggestions=suggestions
    )
    
    # Optionally save to database for analytics
    try:
        await db.anonymous_searches.insert_one(search_response.dict())
    except Exception as e:
        logger.warning(f"Failed to save anonymous search: {e}")
    
    return search_response


# Popular Career Topics endpoint
@api_router.get("/popular-topics")
async def get_popular_topics():
    """Get popular career topics and trending searches"""
    
    # You could make this dynamic by analyzing search history
    # For now, return curated popular topics
    topics = {
        "trending_careers": [
            "AI/Machine Learning Engineer",
            "Data Scientist",
            "Cybersecurity Specialist",
            "Product Manager",
            "UX/UI Designer",
            "Cloud Engineer",
            "Digital Marketing Specialist",
            "Software Developer"
        ],
        "popular_questions": [
            "How to break into tech without a CS degree?",
            "What skills do I need for data science?",
            "How to transition careers at 30+?",
            "Remote work opportunities in marketing",
            "Highest paying entry-level jobs",
            "How to negotiate salary?",
            "Best certifications for career growth",
            "How to build a professional network?"
        ],
        "industry_insights": [
            "Technology",
            "Healthcare",
            "Finance",
            "Education",
            "Manufacturing",
            "Renewable Energy",
            "E-commerce",
            "Biotechnology"
        ]
    }
    
    return topics


# Add basic endpoints
@api_router.get("/")
async def root():
    return {"message": "Career Advisor API - Empowering your career journey with AI"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "career-advisor-api"}

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    education_level: str  # High School, Bachelor's, Master's, PhD, etc.
    field_of_study: Optional[str] = None
    skills: List[str] = []
    experience_years: int = 0
    current_role: Optional[str] = None
    career_interests: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserProfileCreate(BaseModel):
    name: str
    education_level: str
    field_of_study: Optional[str] = None
    skills: List[str] = []
    experience_years: int = 0
    current_role: Optional[str] = None
    career_interests: List[str] = []

class JobAnalysisRequest(BaseModel):
    user_id: str
    job_description: str

class JobAnalysisResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    job_description: str
    analysis: Dict[str, Any]
    recommendations: List[str]
    match_score: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CareerAdviceRequest(BaseModel):
    user_id: str
    query: str

class CareerAdviceResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    query: str
    advice: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Helper function to get OpenAI response
async def get_ai_response(system_message: str, user_message: str) -> str:
    try:
        chat = LlmChat(
            api_key=os.environ.get('OPENAI_API_KEY'),
            session_id=str(uuid.uuid4()),
            system_message=system_message
        ).with_model("openai", "gpt-4o")
        
        message = UserMessage(text=user_message)
        response = await chat.send_message(message)
        return response
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise HTTPException(status_code=500, detail="AI service unavailable")


# User Profile endpoints
@api_router.post("/profiles", response_model=UserProfile)
async def create_profile(profile_data: UserProfileCreate):
    profile_dict = profile_data.dict()
    profile = UserProfile(**profile_dict)
    await db.user_profiles.insert_one(profile.dict())
    return profile

@api_router.get("/profiles", response_model=List[UserProfile])
async def get_profiles():
    profiles = await db.user_profiles.find().to_list(1000)
    return [UserProfile(**profile) for profile in profiles]

@api_router.get("/profiles/{user_id}", response_model=UserProfile)
async def get_profile(user_id: str):
    profile = await db.user_profiles.find_one({"id": user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return UserProfile(**profile)

@api_router.put("/profiles/{user_id}", response_model=UserProfile)
async def update_profile(user_id: str, profile_data: UserProfileCreate):
    existing_profile = await db.user_profiles.find_one({"id": user_id})
    if not existing_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    updated_data = profile_data.dict()
    updated_data["id"] = user_id
    updated_data["created_at"] = existing_profile["created_at"]
    
    updated_profile = UserProfile(**updated_data)
    await db.user_profiles.replace_one({"id": user_id}, updated_profile.dict())
    return updated_profile


# Job Analysis endpoints
@api_router.post("/analyze-job", response_model=JobAnalysisResult)
async def analyze_job(request: JobAnalysisRequest):
    # Get user profile
    profile = await db.user_profiles.find_one({"id": request.user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    user_profile = UserProfile(**profile)
    
    # Create system message for job analysis
    system_message = """You are an expert career advisor. Analyze job descriptions and provide detailed insights about:
1. Required qualifications (education, skills, experience)
2. Job responsibilities and requirements
3. Career level and growth potential
4. Salary expectations (if mentioned)
5. Company culture indicators
6. Match assessment for the given user profile

Respond in JSON format with the following structure:
{
    "required_education": "education level needed",
    "required_skills": ["skill1", "skill2"],
    "required_experience": "years of experience needed", 
    "responsibilities": ["responsibility1", "responsibility2"],
    "career_level": "entry/mid/senior level",
    "growth_potential": "description of growth opportunities",
    "salary_range": "salary information if available",
    "company_culture": "culture indicators",
    "match_assessment": "detailed assessment of user fit"
}"""
    
    # Create user message with job description and profile
    user_message = f"""
    Please analyze this job description:
    
    {request.job_description}
    
    For this user profile:
    - Name: {user_profile.name}
    - Education: {user_profile.education_level}
    - Field of Study: {user_profile.field_of_study}
    - Skills: {', '.join(user_profile.skills)}
    - Experience: {user_profile.experience_years} years
    - Current Role: {user_profile.current_role}
    - Career Interests: {', '.join(user_profile.career_interests)}
    """
    
    # Get AI analysis
    ai_response = await get_ai_response(system_message, user_message)
    
    # Parse AI response (assuming it returns JSON-like text)
    try:
        import json
        analysis = json.loads(ai_response)
    except:
        # If JSON parsing fails, create structured response
        analysis = {
            "analysis_text": ai_response,
            "parsed": False
        }
    
    # Generate recommendations based on analysis
    recommendations_prompt = f"""Based on the job analysis, provide 3-5 specific recommendations for the user to improve their candidacy for this role. Consider their current profile and what's missing."""
    
    recommendations_response = await get_ai_response(
        "You are a career coach providing actionable advice.",
        recommendations_prompt + f"\n\nJob Analysis: {ai_response}\n\nUser Profile: {user_message}"
    )
    
    # Calculate match score (simplified - you can enhance this)
    match_score = 0.75  # This would be calculated based on actual analysis
    
    # Save analysis result
    result = JobAnalysisResult(
        user_id=request.user_id,
        job_description=request.job_description,
        analysis=analysis,
        recommendations=recommendations_response.split('\n') if recommendations_response else [],
        match_score=match_score
    )
    
    await db.job_analyses.insert_one(result.dict())
    return result

@api_router.get("/job-analyses/{user_id}")
async def get_user_job_analyses(user_id: str):
    analyses = await db.job_analyses.find({"user_id": user_id}).to_list(100)
    return [JobAnalysisResult(**analysis) for analysis in analyses]


# Career Advice endpoints
@api_router.post("/career-advice", response_model=CareerAdviceResponse)
async def get_career_advice(request: CareerAdviceRequest):
    # Get user profile
    profile = await db.user_profiles.find_one({"id": request.user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    user_profile = UserProfile(**profile)
    
    # Create system message for career advice
    system_message = """You are an expert career advisor with deep knowledge of various industries, job markets, and career paths. Provide personalized, actionable career advice based on the user's profile and specific questions. Your advice should be:
1. Practical and actionable
2. Based on current job market trends
3. Tailored to their education and experience level
4. Encouraging yet realistic
5. Include specific next steps they can take"""
    
    # Create user message with query and profile context
    user_message = f"""
    User Question: {request.query}
    
    User Profile Context:
    - Name: {user_profile.name}
    - Education: {user_profile.education_level} in {user_profile.field_of_study}
    - Skills: {', '.join(user_profile.skills)}
    - Experience: {user_profile.experience_years} years
    - Current Role: {user_profile.current_role}
    - Career Interests: {', '.join(user_profile.career_interests)}
    
    Please provide detailed career advice addressing their question.
    """
    
    # Get AI advice
    advice = await get_ai_response(system_message, user_message)
    
    # Save advice
    advice_response = CareerAdviceResponse(
        user_id=request.user_id,
        query=request.query,
        advice=advice
    )
    
    await db.career_advice.insert_one(advice_response.dict())
    return advice_response

@api_router.get("/career-advice/{user_id}")
async def get_user_career_advice(user_id: str):
    advice_list = await db.career_advice.find({"user_id": user_id}).to_list(100)
    return [CareerAdviceResponse(**advice) for advice in advice_list]


# Market Insights endpoint
@api_router.get("/market-insights/{field}")
async def get_market_insights(field: str):
    system_message = """You are a job market analyst. Provide current insights about specific fields including:
1. Job market trends
2. In-demand skills
3. Salary ranges
4. Growth outlook
5. Top companies hiring
6. Emerging opportunities"""
    
    user_message = f"Provide comprehensive job market insights for the {field} field in 2025."
    
    insights = await get_ai_response(system_message, user_message)
    
    return {
        "field": field,
        "insights": insights,
        "generated_at": datetime.utcnow()
    }

# Degree Programs to Career Mapping endpoint
@api_router.get("/degree-programs")
async def get_degree_programs():
    """Get comprehensive mapping of degree programs to career opportunities"""
    
    degree_mappings = {
        "stem_fields": {
            "Computer Science": {
                "direct_careers": [
                    "Software Developer/Engineer",
                    "Data Scientist",
                    "AI/Machine Learning Engineer",
                    "Cybersecurity Specialist",
                    "DevOps Engineer",
                    "Product Manager (Technical)",
                    "Research Scientist"
                ],
                "alternative_paths": [
                    "Digital Marketing Specialist",
                    "Technical Writer",
                    "IT Consultant",
                    "Startup Founder",
                    "Technical Sales Engineer"
                ],
                "skills_gap": [
                    "Industry-specific domain knowledge",
                    "Soft skills and communication",
                    "Project management",
                    "Cloud platforms proficiency",
                    "Advanced system design"
                ]
            },
            "Data Science/Statistics": {
                "direct_careers": [
                    "Data Scientist",
                    "Data Analyst",
                    "Business Intelligence Analyst",
                    "Research Analyst",
                    "Quantitative Analyst",
                    "Machine Learning Engineer"
                ],
                "alternative_paths": [
                    "Product Manager",
                    "Management Consultant",
                    "Risk Analyst",
                    "Marketing Analyst",
                    "Operations Research Analyst"
                ],
                "skills_gap": [
                    "Domain expertise in target industry",
                    "Advanced programming skills",
                    "Big data technologies",
                    "Data visualization tools",
                    "Business communication skills"
                ]
            },
            "Engineering (General)": {
                "direct_careers": [
                    "Design Engineer",
                    "Project Engineer",
                    "Systems Engineer",
                    "Quality Engineer",
                    "Manufacturing Engineer",
                    "Research & Development Engineer"
                ],
                "alternative_paths": [
                    "Technical Product Manager",
                    "Engineering Consultant",
                    "Patent Attorney",
                    "Technical Sales",
                    "Startup Founder"
                ],
                "skills_gap": [
                    "Industry certifications",
                    "Project management",
                    "Modern software tools",
                    "Business acumen",
                    "Leadership skills"
                ]
            }
        },
        "business_fields": {
            "Business Administration/Management": {
                "direct_careers": [
                    "Business Analyst",
                    "Project Manager",
                    "Operations Manager",
                    "HR Manager",
                    "Marketing Manager",
                    "Financial Analyst"
                ],
                "alternative_paths": [
                    "Management Consultant",
                    "Product Manager",
                    "Entrepreneur",
                    "Sales Manager",
                    "Business Development"
                ],
                "skills_gap": [
                    "Industry-specific knowledge",
                    "Advanced analytics",
                    "Digital marketing",
                    "Data analysis tools",
                    "Technical literacy"
                ]
            },
            "Economics": {
                "direct_careers": [
                    "Economic Analyst",
                    "Financial Analyst",
                    "Policy Analyst",
                    "Research Economist",
                    "Market Research Analyst"
                ],
                "alternative_paths": [
                    "Data Scientist",
                    "Investment Banking",
                    "Management Consultant",
                    "Business Development",
                    "Government Positions"
                ],
                "skills_gap": [
                    "Programming (Python/R)",
                    "Advanced statistical software",
                    "Database management",
                    "Financial modeling",
                    "Industry regulations"
                ]
            },
            "Marketing": {
                "direct_careers": [
                    "Digital Marketing Specialist",
                    "Brand Manager",
                    "Content Marketing Manager",
                    "Social Media Manager",
                    "Marketing Analyst"
                ],
                "alternative_paths": [
                    "Product Manager",
                    "UX Researcher",
                    "Business Development",
                    "Sales Manager",
                    "PR Specialist"
                ],
                "skills_gap": [
                    "Data analytics and metrics",
                    "Marketing automation tools",
                    "SEO/SEM expertise",
                    "A/B testing",
                    "Customer psychology"
                ]
            }
        },
        "liberal_arts": {
            "Psychology": {
                "direct_careers": [
                    "Clinical Psychologist",
                    "Counseling Psychologist",
                    "UX Researcher",
                    "HR Specialist",
                    "Market Research Analyst"
                ],
                "alternative_paths": [
                    "Product Manager",
                    "Data Analyst",
                    "Social Media Manager",
                    "Training Coordinator",
                    "Sales Representative"
                ],
                "skills_gap": [
                    "Research methodology",
                    "Statistical analysis software",
                    "Business knowledge",
                    "Technology tools",
                    "Industry certifications"
                ]
            },
            "Communication": {
                "direct_careers": [
                    "Public Relations Specialist",
                    "Content Writer",
                    "Digital Marketing Manager",
                    "Social Media Manager",
                    "Corporate Communications"
                ],
                "alternative_paths": [
                    "UX Writer",
                    "Product Marketing Manager",
                    "Training Specialist",
                    "Event Coordinator",
                    "Business Analyst"
                ],
                "skills_gap": [
                    "Digital marketing tools",
                    "Data analysis",
                    "SEO knowledge",
                    "Design basics",
                    "Project management"
                ]
            }
        },
        "healthcare_fields": {
            "Biology/Biomedical Sciences": {
                "direct_careers": [
                    "Research Scientist",
                    "Laboratory Technician",
                    "Quality Control Analyst",
                    "Biomedical Engineer",
                    "Clinical Research Coordinator"
                ],
                "alternative_paths": [
                    "Pharmaceutical Sales",
                    "Science Writer",
                    "Patent Analyst",
                    "Regulatory Affairs",
                    "Biotech Consultant"
                ],
                "skills_gap": [
                    "Regulatory knowledge",
                    "Business skills",
                    "Advanced instrumentation",
                    "Data analysis",
                    "Project management"
                ]
            }
        }
    }
    
    return degree_mappings


# Enhanced Degree-Career Search endpoint
@api_router.post("/degree-career-search")
async def degree_career_search(request: dict):
    """
    AI-powered search specifically for connecting degrees to careers
    """
    degree = request.get('degree', '')
    career_interest = request.get('career_interest', '')
    
    system_message = """You are a specialized academic and career counselor. Help students understand the connection between their degree program and career opportunities. Provide:

1. **Direct Career Paths**: Jobs directly related to the degree
2. **Alternative Career Paths**: Unexpected but viable career options
3. **Skills Development**: What skills to develop beyond coursework
4. **Education Enhancement**: Additional certifications, minors, or courses to consider
5. **Timeline**: Realistic timeline from graduation to career establishment
6. **Success Stories**: Examples of graduates who succeeded in various paths
7. **Action Steps**: Specific next steps the student can take now

Make your response practical, encouraging, and actionable."""
    
    user_message = f"""
    Student's Degree Program: {degree}
    Career Interest/Area: {career_interest}
    
    Please provide comprehensive guidance on how this degree can lead to career success, including both traditional and non-traditional paths.
    """
    
    response = await get_ai_response(system_message, user_message)
    
    return {
        "degree": degree,
        "career_interest": career_interest,
        "guidance": response,
        "generated_at": datetime.utcnow().isoformat()
    }


# Add basic endpoints
@api_router.get("/")
async def root():
    return {"message": "Career Advisor API - Empowering your career journey with AI"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "career-advisor-api"}

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()