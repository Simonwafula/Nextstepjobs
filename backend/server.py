from fastapi import FastAPI, APIRouter, HTTPException
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
from datetime import datetime
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


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
    return {"message": "Hello World"}
    return {"message": "Career Advisor API - Empowering your career journey with AI"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

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
