from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
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
app = FastAPI(
    title="NextStep API",
    description="Your AI-powered career evolution partner - transforming professional journeys with intelligent insights",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

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