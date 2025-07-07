"""
NextStep Job Processing Pipeline
Processes scraped job listings and extracts structured information
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
import re
import logging
from datetime import datetime, timedelta
import json
from emergentintegrations.llm.chat import LlmChat, UserMessage
import os
logger = logging.getLogger(__name__)

class JobProcessor:
    """
    Advanced job processing pipeline for NextStep
    Extracts structured information from job listings
    """
<<<<<<< HEAD

=======
    
>>>>>>> update/main
    def __init__(self):
        self.session = None
        self.ai_client = None
        self._init_ai_client()
<<<<<<< HEAD

    def _init_ai_client(self):
        """Initialize AI client for content processing"""

# Enhanced data models with validation
class JobClassification(BaseModel):
    category: Optional[str] = None
    level: Optional[str] = None
    function: Optional[str] = None
    department: Optional[str] = None

    @validator('level')
    def validate_level(cls, v):
        if v:
            valid_levels = ['entry', 'junior', 'mid', 'senior', 'lead', 'manager', 'director', 'executive']
            v_lower = v.lower()
            for level in valid_levels:
                if level in v_lower:
                    return level.title()
        return v


class LocationWork(BaseModel):
    office_location: Optional[str] = None
    remote: Optional[bool] = None
    onsite: Optional[bool] = None
    hybrid: Optional[bool] = None
    travel_required: Optional[str] = None

    @validator('office_location')
    def clean_location(cls, v):
        if v:
            return v.strip().title()
        return v


class SkillsTaxonomy(BaseModel):
    main_skill: Optional[str] = None
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    tools_technologies: List[str] = Field(default_factory=list)
    programming_languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)

    @validator('technical_skills', 'soft_skills', 'tools_technologies',
               'programming_languages', 'frameworks', pre=True)
    def clean_skills_list(cls, v):
        if isinstance(v, str):
            return [skill.strip() for skill in v.split(',') if skill.strip()]
        elif isinstance(v, list):
            return [skill.strip() for skill in v if skill and skill.strip()]
        return []


class Certification(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    year: Optional[int] = None
    required: Optional[bool] = False

    @validator('year')
    def validate_year(cls, v):
        if v and (v < 1950 or v > datetime.now().year + 5):
            return None
        return v


class CareerProgression(BaseModel):
    entry_level: Optional[str] = None
    mid_level: Optional[str] = None
    senior_level: Optional[str] = None
    growth_opportunities: List[str] = Field(default_factory=list)


class CompensationBenefits(BaseModel):
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = "USD"
    salary_type: Optional[str] = None  # hourly, annual, contract
    benefits: List[str] = Field(default_factory=list)

    @validator('salary_min', 'salary_max')
    def validate_salary(cls, v):
        if v and (v < 0 or v > 10000000):  # Reasonable bounds for salary
            return None
        return v


class EducationRequirement(BaseModel):
    level: Literal[
        "high_school", "certificate", "diploma", "associate",
        "bachelor", "master", "phd", "professional_license",
        "none_specified", "equivalent_experience"
    ]
    field: Optional[str] = None
    requirement_type: Literal["required", "preferred", "equivalent_experience_accepted"]
    years_experience_substitute: Optional[int] = None
    confidence_score: float = Field(ge=0.0, le=1.0)

    @validator('field')
    def clean_field(cls, v):
        if v:
            return v.lower().strip()
        return v


class EducationExtraction(BaseModel):
    requirements: List[EducationRequirement]
    raw_text_analyzed: str


class JobExtraction(BaseModel):
    # Basic fields with validation
    title_clean: Optional[str] = None
    company: Optional[str] = None
    company_location: Optional[str] = None
    post_date: Optional[str] = None
    industry: Optional[str] = None
    job_type: Optional[str] = None
    job_category: Optional[str] = None
    job_description: Optional[str] = None
    application_deadline: Optional[str] = None
    additional_requirements: Optional[str] = None
    full_link: Optional[str] = None
    experience_required: Optional[str] = None
    company_size: Optional[str] = None

    # Nested structures with defaults
    job_classification: JobClassification = Field(default_factory=JobClassification)
    location_and_work: LocationWork = Field(default_factory=LocationWork)
    skills: SkillsTaxonomy = Field(default_factory=SkillsTaxonomy)
    certifications: List[Certification] = Field(default_factory=list)
    career_progression: CareerProgression = Field(default_factory=CareerProgression)
    compensation: CompensationBenefits = Field(default_factory=CompensationBenefits)
    education_requirements: List[EducationRequirement] = Field(default_factory=list)

    raw_text_analyzed: str = Field(default="")
    processing_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

    @validator('full_link')
    def validate_url(cls, v):
        if v and not URL_RE.match(v):
            logger.warning(f"Invalid URL format: {v}")
        return v

    @validator('post_date', 'application_deadline')
    def validate_dates(cls, v):
        if v:
            try:
                # Try to parse common date formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%B %d, %Y']:
                    try:
                        datetime.strptime(v, fmt)
                        return v
                    except ValueError:
                        continue
                logger.warning(f"Could not parse date: {v}")
            except Exception:
                pass
        return v


class AcademicDetailsProcessor:
    def __init__(
            self,
            input_db_path: str = "db/jobs.sqlite3",
            output_db_path: str = "db/processed_jobs.sqlite3",
            llm_model: str = "gpt-4o-mini",
            temperature: float = 0.1,
            api_key: Optional[str] = None,
            batch_size: int = 10,
            max_retries: int = 3
    ):
        self.input_db_path = input_db_path
        self.output_db_path = output_db_path
        self.batch_size = batch_size
        self.max_retries = max_retries

        # Initialize API key
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OpenAI API key must be set via parameter or OPENAI_API_KEY env var")

        # Initialize LLM and parsers
        self.llm = OpenAI(model=llm_model, temperature=temperature, openai_api_key=key)
        self.job_parser = PydanticOutputParser(pydantic_object=JobExtraction)
        self.education_parser = PydanticOutputParser(pydantic_object=EducationExtraction)

        # Create processing chains
        self.job_chain = self._create_job_chain()
        self.education_chain = self._create_education_chain()

        # Setup database
        self._setup_db()

        logger.info(f"Processor initialized with model: {llm_model}")

    def _create_job_chain(self) -> RunnableSequence:
        """Create the job extraction chain"""
        prompt = PromptTemplate.from_template(
            """Extract comprehensive job information from the following job posting.

            Focus on extracting:
            1. Basic job details (title, company, location, dates)
            2. Job classification (category, level, function, department)
            3. Work arrangement (remote/onsite/hybrid, location details)
            4. Skills taxonomy (technical skills, soft skills, tools, programming languages, frameworks)
            5. Certifications (name, issuer, whether required)
            6. Career progression opportunities
            7. Compensation and benefits
            8. Experience requirements

            Be thorough but accurate. If information is not clearly stated, use null/empty values.

            Job Posting Text:
            {text}

            {format_instructions}"""
        )
        return prompt | self.llm | self.job_parser

    def _create_education_chain(self) -> RunnableSequence:
        """Create the education requirements extraction chain"""
        prompt = PromptTemplate.from_template(
            """Analyze the job posting and extract all education requirements.

            For each education requirement, determine:
            1. Education level (high_school, certificate, diploma, associate, bachelor, master, phd, professional_license, none_specified, equivalent_experience)
            2. Field of study (if specified)
            3. Whether it's required, preferred, or equivalent experience is accepted
            4. How many years of experience can substitute for the education
            5. Confidence score (0.0-1.0) for the extraction accuracy

            Consider phrases like:
            - "Bachelor's degree required" → required
            - "Master's preferred" → preferred  
            - "Degree or equivalent experience" → equivalent_experience_accepted
            - "5 years experience in lieu of degree" → years_experience_substitute: 5

            Job Posting Text:
            {text}

            {format_instructions}"""
        )
        return prompt | self.llm | self.education_parser

    def _setup_db(self):
        """Setup the output database with improved schema"""
        conn = sqlite3.connect(self.output_db_path)

        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")

        # Main jobs table with additional fields
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS jobs_meta
                     (
                         job_id
                         INTEGER
                         PRIMARY
                         KEY,
                         full_link
                         TEXT,
                         title_clean
                         TEXT,
                         company
                         TEXT,
                         company_location
                         TEXT,
                         post_date
                         TEXT,
                         industry
                         TEXT,
                         job_type
                         TEXT,
                         job_category
                         TEXT,
                         job_description
                         TEXT,
                         application_deadline
                         TEXT,
                         additional_requirements
                         TEXT,
                         experience_required
                         TEXT,
                         company_size
                         TEXT,
                         processing_timestamp
                         TEXT,
                         created_at
                         TIMESTAMP
                         DEFAULT
                         CURRENT_TIMESTAMP,
                         updated_at
                         TIMESTAMP
                         DEFAULT
                         CURRENT_TIMESTAMP
                     )
                     """)

        # Add indexes for better performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_meta_job ON jobs_meta(job_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_meta_company ON jobs_meta(company)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_meta_industry ON jobs_meta(industry)")

        # Job classification table
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS job_classification
                     (
                         job_id
                         INTEGER
                         PRIMARY
                         KEY,
                         category
                         TEXT,
                         level
                         TEXT,
                         function
                         TEXT,
                         department
                         TEXT,
                         FOREIGN
                         KEY
                     (
                         job_id
                     ) REFERENCES jobs_meta
                     (
                         job_id
                     ) ON DELETE CASCADE
                         )
                     """)

        # Location and work arrangement
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS location_work
                     (
                         job_id
                         INTEGER
                         PRIMARY
                         KEY,
                         office_location
                         TEXT,
                         remote
                         BOOLEAN,
                         onsite
                         BOOLEAN,
                         hybrid
                         BOOLEAN,
                         travel_required
                         TEXT,
                         FOREIGN
                         KEY
                     (
                         job_id
                     ) REFERENCES jobs_meta
                     (
                         job_id
                     ) ON DELETE CASCADE
                         )
                     """)

        # Enhanced skills taxonomy
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS skills_taxonomy
                     (
                         job_id
                         INTEGER
                         PRIMARY
                         KEY,
                         main_skill
                         TEXT,
                         technical_skills
                         TEXT,
                         soft_skills
                         TEXT,
                         tools_technologies
                         TEXT,
                         programming_languages
                         TEXT,
                         frameworks
                         TEXT,
                         FOREIGN
                         KEY
                     (
                         job_id
                     ) REFERENCES jobs_meta
                     (
                         job_id
                     ) ON DELETE CASCADE
                         )
                     """)

        # Certifications table
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS certifications
                     (
                         id
                         INTEGER
                         PRIMARY
                         KEY
                         AUTOINCREMENT,
                         job_id
                         INTEGER,
                         name
                         TEXT,
                         issuer
                         TEXT,
                         year
                         INTEGER,
                         required
                         BOOLEAN
                         DEFAULT
                         FALSE,
                         FOREIGN
                         KEY
                     (
                         job_id
                     ) REFERENCES jobs_meta
                     (
                         job_id
                     ) ON DELETE CASCADE
                         )
                     """)

        # Career progression
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS career_progression
                     (
                         job_id
                         INTEGER
                         PRIMARY
                         KEY,
                         entry_level
                         TEXT,
                         mid_level
                         TEXT,
                         senior_level
                         TEXT,
                         growth_opportunities
                         TEXT,
                         FOREIGN
                         KEY
                     (
                         job_id
                     ) REFERENCES jobs_meta
                     (
                         job_id
                     ) ON DELETE CASCADE
                         )
                     """)

        # Compensation and benefits
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS compensation
                     (
                         job_id
                         INTEGER
                         PRIMARY
                         KEY,
                         salary_min
                         REAL,
                         salary_max
                         REAL,
                         currency
                         TEXT
                         DEFAULT
                         'USD',
                         salary_type
                         TEXT,
                         benefits
                         TEXT,
                         FOREIGN
                         KEY
                     (
                         job_id
                     ) REFERENCES jobs_meta
                     (
                         job_id
                     ) ON DELETE CASCADE
                         )
                     """)

        # Education requirements table
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS education_requirements
                     (
                         id
                         INTEGER
                         PRIMARY
                         KEY
                         AUTOINCREMENT,
                         job_id
                         INTEGER
                         NOT
                         NULL,
                         level
                         TEXT
                         NOT
                         NULL,
                         field
                         TEXT,
                         requirement_type
                         TEXT
                         NOT
                         NULL,
                         years_experience_substitute
                         INTEGER,
                         confidence_score
                         REAL
                         NOT
                         NULL,
                         FOREIGN
                         KEY
                     (
                         job_id
                     ) REFERENCES jobs_meta
                     (
                         job_id
                     ) ON DELETE CASCADE
                         )
                     """)

        # Processing status table for tracking
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS processing_status
                     (
                         job_id
                         INTEGER
                         PRIMARY
                         KEY,
                         status
                         TEXT
                         DEFAULT
                         'pending',
                         error_message
                         TEXT,
                         retry_count
                         INTEGER
                         DEFAULT
                         0,
                         last_attempt
                         TIMESTAMP
                         DEFAULT
                         CURRENT_TIMESTAMP,
                         FOREIGN
                         KEY
                     (
                         job_id
                     ) REFERENCES jobs_meta
                     (
                         job_id
                     ) ON DELETE CASCADE
                         )
                     """)

        # Add indexes for performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_edu_job ON education_requirements(job_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cert_job ON certifications(job_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON processing_status(status)")

        conn.commit()
        conn.close()
        logger.info("Database schema setup completed")

    def _preprocess_text(self, text: str) -> str:
        """Preprocess job posting text"""
        if not text:
            return ""

        # Normalize whitespace
        text = WHITESPACE_RE.sub(" ", text)

        # Normalize degree abbreviations
        for regex, replacement in [
            (BS_RE, "Bachelor of Science"),
            (BA_RE, "Bachelor of Arts"),
            (MS_RE, "Master of Science"),
            (MA_RE, "Master of Arts"),
            (PHD_RE, "Doctor of Philosophy")
        ]:
            text = regex.sub(replacement, text)

        return text.strip()

    def _store_job_data(self, job_id: int, job_data: JobExtraction, education_data: EducationExtraction):
        """Store extracted job data in database"""
        conn = sqlite3.connect(self.output_db_path)

        try:
            self.ai_client = LlmChat(api_key=os.environ.get('OPENAI_API_KEY'))
            conn.execute("BEGIN TRANSACTION")

            # Store main job metadata
            conn.execute("""
                INSERT OR REPLACE INTO jobs_meta 
                (job_id, full_link, title_clean, company, company_location, post_date, 
                 industry, job_type, job_category, job_description, application_deadline, 
                 additional_requirements, experience_required, company_size, processing_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id, job_data.full_link, job_data.title_clean, job_data.company,
                job_data.company_location, job_data.post_date, job_data.industry,
                job_data.job_type, job_data.job_category, job_data.job_description,
                job_data.application_deadline, job_data.additional_requirements,
                job_data.experience_required, job_data.company_size, job_data.processing_timestamp
            ))

            # Store job classification
            conn.execute("""
                INSERT OR REPLACE INTO job_classification 
                (job_id, category, level, function, department)
                VALUES (?, ?, ?, ?, ?)
            """, (
                job_id, job_data.job_classification.category,
                job_data.job_classification.level, job_data.job_classification.function,
                job_data.job_classification.department
            ))

            # Store location and work details
            conn.execute("""
                INSERT OR REPLACE INTO location_work 
                (job_id, office_location, remote, onsite, hybrid, travel_required)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                job_id, job_data.location_and_work.office_location,
                job_data.location_and_work.remote, job_data.location_and_work.onsite,
                job_data.location_and_work.hybrid, job_data.location_and_work.travel_required
            ))

            # Store skills taxonomy
            conn.execute("""
                INSERT OR REPLACE INTO skills_taxonomy 
                (job_id, main_skill, technical_skills, soft_skills, tools_technologies, 
                 programming_languages, frameworks)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id, job_data.skills.main_skill,
                json.dumps(job_data.skills.technical_skills),
                json.dumps(job_data.skills.soft_skills),
                json.dumps(job_data.skills.tools_technologies),
                json.dumps(job_data.skills.programming_languages),
                json.dumps(job_data.skills.frameworks)
            ))

            # Clear and store certifications
            conn.execute("DELETE FROM certifications WHERE job_id = ?", (job_id,))
            for cert in job_data.certifications:
                conn.execute("""
                             INSERT INTO certifications (job_id, name, issuer, year, required)
                             VALUES (?, ?, ?, ?, ?)
                             """, (job_id, cert.name, cert.issuer, cert.year, cert.required))

            # Store career progression
            conn.execute("""
                INSERT OR REPLACE INTO career_progression 
                (job_id, entry_level, mid_level, senior_level, growth_opportunities)
                VALUES (?, ?, ?, ?, ?)
            """, (
                job_id, job_data.career_progression.entry_level,
                job_data.career_progression.mid_level, job_data.career_progression.senior_level,
                json.dumps(job_data.career_progression.growth_opportunities)
            ))

            # Store compensation
            conn.execute("""
                INSERT OR REPLACE INTO compensation 
                (job_id, salary_min, salary_max, currency, salary_type, benefits)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                job_id, job_data.compensation.salary_min, job_data.compensation.salary_max,
                job_data.compensation.currency, job_data.compensation.salary_type,
                json.dumps(job_data.compensation.benefits)
            ))

            # Clear and store education requirements
            conn.execute("DELETE FROM education_requirements WHERE job_id = ?", (job_id,))
            for req in education_data.requirements:
                conn.execute("""
                             INSERT INTO education_requirements
                             (job_id, level, field, requirement_type, years_experience_substitute, confidence_score)
                             VALUES (?, ?, ?, ?, ?, ?)
                             """, (
                                 job_id, req.level, req.field, req.requirement_type,
                                 req.years_experience_substitute, req.confidence_score
                             ))

            # Update processing status
            conn.execute("""
                INSERT OR REPLACE INTO processing_status (job_id, status, last_attempt)
                VALUES (?, 'completed', CURRENT_TIMESTAMP)
            """, (job_id,))

            conn.commit()
            logger.info(f"Successfully stored data for job {job_id}")

        except Exception as e:
            logger.error(f"Failed to initialize AI client: {e}")

=======
        
    def _init_ai_client(self):
        """Initialize AI client for content processing"""
        try:
            self.ai_client = LlmChat(api_key=os.environ.get('OPENAI_API_KEY'))
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {e}")
            
>>>>>>> update/main
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=3)
        timeout = aiohttp.ClientTimeout(total=60)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'NextStep Job Processor 1.0 (+https://nextstep.co.ke)'
            }
        )
        return self
<<<<<<< HEAD

=======
        
>>>>>>> update/main
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
<<<<<<< HEAD

    async def process_job(self, job_record: Dict) -> Dict:
        """
        Process a single job record and extract structured information

        Args:
            job_record: Basic job data with title and link

=======
            
    async def process_job(self, job_record: Dict) -> Dict:
        """
        Process a single job record and extract structured information
        
        Args:
            job_record: Basic job data with title and link
            
>>>>>>> update/main
        Returns:
            Processed job data with extracted information
        """
        try:
            logger.info(f"Processing job: {job_record.get('title', 'Unknown')}")
<<<<<<< HEAD

=======
            
>>>>>>> update/main
            # Fetch full job content
            job_content = await self._fetch_job_content(job_record['link'])
            if not job_content:
                logger.warning(f"Failed to fetch content for {job_record['link']}")
                return self._create_failed_record(job_record, "Failed to fetch content")
<<<<<<< HEAD

            # Extract structured information
            extracted_data = await self._extract_job_information(job_content, job_record)

            # Enhance with AI analysis
            ai_enhanced_data = await self._enhance_with_ai(extracted_data, job_content)

            # Create final processed record
            processed_record = self._create_processed_record(job_record, extracted_data, ai_enhanced_data)

            logger.info(f"Successfully processed job: {processed_record['title']}")
            return processed_record

        except Exception as e:
            logger.error(f"Error processing job {job_record.get('link', 'Unknown')}: {e}")
            return self._create_failed_record(job_record, str(e))

    async def _fetch_job_content(self, job_url: str) -> Optional[str]:
        """Fetch full job posting content"""
            conn.rollback()
            logger.error(f"Failed to store data for job {job_id}: {e}")

            # Update error status
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO processing_status 
                    (job_id, status, error_message, retry_count, last_attempt)
                    VALUES (?, 'error', ?, COALESCE((SELECT retry_count FROM processing_status WHERE job_id = ?), 0) + 1, CURRENT_TIMESTAMP)
                """, (job_id, str(e), job_id))
                conn.commit()
            except:
                pass

            raise
        finally:
            conn.close()

    def extract_and_store(self, job_id: int, full_link: str, content: str) -> tuple[JobExtraction, EducationExtraction]:
        """Extract job information and education requirements, then store in database"""
        processed_content = self._preprocess_text(content)

        if not processed_content:
            logger.warning(f"Job {job_id}: Empty content after preprocessing")
            return JobExtraction(), EducationExtraction(requirements=[], raw_text_analyzed="")

        retry_count = 0
        while retry_count < self.max_retries:
            try:
                # Extract job information
                job_data = self.job_chain.invoke({
                    "text": processed_content,
                    "format_instructions": self.job_parser.get_format_instructions()
                })
                job_data.full_link = full_link
                job_data.raw_text_analyzed = content[:1000]  # Store first 1000 chars

                # Extract education requirements
                education_data = self.education_chain.invoke({
                    "text": processed_content,
                    "format_instructions": self.education_parser.get_format_instructions()
                })
                education_data.raw_text_analyzed = content[:500]

                # Store in database
                self._store_job_data(job_id, job_data, education_data)

                logger.info(
                    f"Job {job_id}: Successfully processed with {len(education_data.requirements)} education requirements")
                return job_data, education_data

            except Exception as e:
                retry_count += 1
                logger.error(f"Job {job_id}: Attempt {retry_count} failed: {e}")

                if retry_count >= self.max_retries:
                    logger.error(f"Job {job_id}: Max retries exceeded")
                    # Return empty structures on final failure
                    empty_job = JobExtraction(
                        full_link=full_link,
                        raw_text_analyzed=content[:1000] if content else ""
                    )
                    empty_education = EducationExtraction(
                        requirements=[],
                        raw_text_analyzed=content[:500] if content else ""
                    )
                    return empty_job, empty_education

                # Wait before retry
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff

    def get_unprocessed_jobs(self) -> List[tuple]:
        """Get jobs that haven't been processed yet or failed processing"""
        input_conn = sqlite3.connect(self.input_db_path)
        output_conn = sqlite3.connect(self.output_db_path)

        # Get jobs that are not in the processed database or have failed
        query = """
                SELECT jd.id, jd.full_link, jd.content
                FROM jobs_data jd
                         LEFT JOIN processing_status ps ON jd.id = ps.job_id
                WHERE ps.job_id IS NULL
                   OR ps.status = 'error'
                   OR (ps.status = 'pending' AND ps.retry_count < ?)
                ORDER BY jd.id \
                """

=======
            
            # Extract structured information
            extracted_data = await self._extract_job_information(job_content, job_record)
            
            # Enhance with AI analysis
            ai_enhanced_data = await self._enhance_with_ai(extracted_data, job_content)
            
            # Create final processed record
            processed_record = self._create_processed_record(job_record, extracted_data, ai_enhanced_data)
            
            logger.info(f"Successfully processed job: {processed_record['title']}")
            return processed_record
            
        except Exception as e:
            logger.error(f"Error processing job {job_record.get('link', 'Unknown')}: {e}")
            return self._create_failed_record(job_record, str(e))
            
    async def _fetch_job_content(self, job_url: str) -> Optional[str]:
        """Fetch full job posting content"""
>>>>>>> update/main
        try:
            async with self.session.get(job_url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"HTTP {response.status} for {job_url}")
                    return None
<<<<<<< HEAD
            rows = input_conn.execute(query, (self.max_retries,)).fetchall()
            logger.info(f"Found {len(rows)} jobs to process")
            return rows
        except sqlite3.Error as e:
            logger.error(f"Error querying unprocessed jobs: {e}")
            return []
        finally:
            input_conn.close()
            output_conn.close()

    def batch_extract(self) -> List[tuple[JobExtraction, EducationExtraction]]:
        """Process jobs in batches"""
        unprocessed_jobs = self.get_unprocessed_jobs()

        if not unprocessed_jobs:
            logger.info("No unprocessed jobs found")
            return []

        results = []

        for i in range(0, len(unprocessed_jobs), self.batch_size):
            batch = unprocessed_jobs[i:i + self.batch_size]
            logger.info(
                f"Processing batch {i // self.batch_size + 1}, jobs {i + 1}-{min(i + self.batch_size, len(unprocessed_jobs))}")

            batch_results = []
            for job_id, full_link, content in batch:
                try:
                    result = self.extract_and_store(job_id, full_link, content)
                    batch_results.append(result)
                except Exception as e:
                    logger.error(f"Failed to process job {job_id}: {e}")
                    batch_results.append((JobExtraction(), EducationExtraction(requirements=[], raw_text_analyzed="")))

            results.extend(batch_results)

            # Small delay between batches to avoid rate limiting
            if i + self.batch_size < len(unprocessed_jobs):
                logger.info("Sleeping 2 seconds between batches...")
                import time
                time.sleep(2)

        logger.info(f"Completed processing {len(results)} jobs")
        return results

    async def extract_and_store_async(self, job_id: int, full_link: str, content: str) -> tuple[
        JobExtraction, EducationExtraction]:
        """Async version of extract_and_store"""
        processed_content = self._preprocess_text(content)

        if not processed_content:
            logger.warning(f"Job {job_id}: Empty content after preprocessing")
            return JobExtraction(), EducationExtraction(requirements=[], raw_text_analyzed="")

        retry_count = 0
        while retry_count < self.max_retries:
            try:
                # Extract job information asynchronously
                job_data = await self.job_chain.ainvoke({
                    "text": processed_content,
                    "format_instructions": self.job_parser.get_format_instructions()
                })
                job_data.full_link = full_link
                job_data.raw_text_analyzed = content[:1000]

                # Extract education requirements asynchronously
                education_data = await self.education_chain.ainvoke({
                    "text": processed_content,
                    "format_instructions": self.education_parser.get_format_instructions()
                })
                education_data.raw_text_analyzed = content[:500]

                # Store in database (synchronous)
                self._store_job_data(job_id, job_data, education_data)

                logger.info(f"[async] Job {job_id}: Successfully processed")
                return job_data, education_data

            except Exception as e:
                retry_count += 1
                logger.error(f"[async] Job {job_id}: Attempt {retry_count} failed: {e}")

                if retry_count >= self.max_retries:
                    logger.error(f"[async] Job {job_id}: Max retries exceeded")
                    empty_job = JobExtraction(full_link=full_link, raw_text_analyzed=content[:1000] if content else "")
                    empty_education = EducationExtraction(requirements=[],
                                                          raw_text_analyzed=content[:500] if content else "")
                    return empty_job, empty_education

                await asyncio.sleep(2 ** retry_count)

    async def batch_extract_async(self, max_concurrent: int = 5) -> List[tuple[JobExtraction, EducationExtraction]]:
        """Process jobs asynchronously with concurrency control"""
        unprocessed_jobs = self.get_unprocessed_jobs()

        if not unprocessed_jobs:
            logger.info("No unprocessed jobs found")
            return []

        # Create semaphore to limit concurrent processing
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(job_data):
            async with semaphore:
                job_id, full_link, content = job_data
                return await self.extract_and_store_async(job_id, full_link, content)

        # Process all jobs concurrently but with limit
        logger.info(f"Starting async processing of {len(unprocessed_jobs)} jobs with max {max_concurrent} concurrent")
        tasks = [process_with_semaphore(job_data) for job_data in unprocessed_jobs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions in results
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                job_id = unprocessed_jobs[i][0]
                logger.error(f"[async] Job {job_id} failed with exception: {result}")
                successful_results.append((JobExtraction(), EducationExtraction(requirements=[], raw_text_analyzed="")))
            else:
                successful_results.append(result)

        logger.info(f"Completed async processing of {len(successful_results)} jobs")
        return successful_results

    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get statistics about the processing pipeline"""
        conn = sqlite3.connect(self.output_db_path)

        try:
            stats = {}

            # Total jobs processed
            stats['total_processed'] = conn.execute("SELECT COUNT(*) FROM jobs_meta").fetchone()[0]

            # Processing status breakdown
            status_counts = conn.execute("""
                                         SELECT status, COUNT(*) as count
                                         FROM processing_status
                                         GROUP BY status
                                         """).fetchall()
            stats['status_breakdown'] = {status: count for status, count in status_counts}

            # Top industries
            industry_counts = conn.execute("""
                                           SELECT industry, COUNT(*) as count
                                           FROM jobs_meta
                                           WHERE industry IS NOT NULL
                                           GROUP BY industry
                                           ORDER BY count DESC
                                               LIMIT 10
                                           """).fetchall()
            stats['top_industries'] = {industry: count for industry, count in industry_counts}

            # Education level distribution
            edu_counts = conn.execute("""
                                      SELECT level, COUNT(*) as count
                                      FROM education_requirements
                                      GROUP BY level
                                      ORDER BY count DESC
                                      """).fetchall()
            stats['education_levels'] = {level: count for level, count in edu_counts}

            # Salary statistics
            salary_stats = conn.execute("""
                                        SELECT AVG(salary_min) as avg_min,
                                               AVG(salary_max) as avg_max,
                                               MIN(salary_min) as min_min,
                                               MAX(salary_max) as max_max,
                                               COUNT(*)        as count_with_salary
                                        FROM compensation
                                        WHERE salary_min IS NOT NULL
                                           OR salary_max IS NOT NULL
                                        """).fetchone()

            if salary_stats and salary_stats[4] > 0:  # count_with_salary > 0
                stats['salary_statistics'] = {
                    'average_min': round(salary_stats[0], 2) if salary_stats[0] else None,
                    'average_max': round(salary_stats[1], 2) if salary_stats[1] else None,
                    'minimum_salary': salary_stats[2],
                    'maximum_salary': salary_stats[3],
                    'jobs_with_salary': salary_stats[4]
                }

            # Remote work statistics
            work_type_stats = conn.execute("""
                                           SELECT SUM(CASE WHEN remote = 1 THEN 1 ELSE 0 END) as remote_jobs,
                                                  SUM(CASE WHEN onsite = 1 THEN 1 ELSE 0 END) as onsite_jobs,
                                                  SUM(CASE WHEN hybrid = 1 THEN 1 ELSE 0 END) as hybrid_jobs,
                                                  COUNT(*)                                    as total_jobs
                                           FROM location_work
                                           """).fetchone()

            if work_type_stats:
                stats['work_arrangement'] = {
                    'remote': work_type_stats[0],
                    'onsite': work_type_stats[1],
                    'hybrid': work_type_stats[2],
                    'total': work_type_stats[3]
                }

            return stats

        except Exception as e:
            logger.error(f"Error fetching {job_url}: {e}")
            return None

=======
        except Exception as e:
            logger.error(f"Error fetching {job_url}: {e}")
            return None
            
>>>>>>> update/main
    async def _extract_job_information(self, html_content: str, job_record: Dict) -> Dict:
        """
        Extract structured information from job posting HTML
        """
        soup = BeautifulSoup(html_content, 'html.parser')
<<<<<<< HEAD

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get clean text
        text_content = soup.get_text(separator=' ', strip=True)

=======
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Get clean text
        text_content = soup.get_text(separator=' ', strip=True)
        
>>>>>>> update/main
        # Initialize extracted data
        extracted = {
            'title': job_record.get('title', ''),
            'company': self._extract_company(soup, text_content),
            'location': self._extract_location(soup, text_content),
            'job_type': self._extract_job_type(text_content),
            'experience_level': self._extract_experience_level(text_content),
            'salary': self._extract_salary(soup, text_content),
            'description': self._extract_description(soup),
            'requirements': self._extract_requirements(text_content),
            'skills': self._extract_skills(text_content),
            'benefits': self._extract_benefits(text_content),
            'deadline': self._extract_deadline(soup, text_content),
            'education': self._extract_education(text_content),
            'industry': self._extract_industry(text_content),
            'full_text': text_content[:5000]  # Limit text length
        }
<<<<<<< HEAD

        return extracted

=======
        
        return extracted
        
>>>>>>> update/main
    def _extract_company(self, soup: BeautifulSoup, text: str) -> str:
        """Extract company name"""
        # Try structured selectors first
        company_selectors = [
            '.company-name', '.company', '[data-testid="company-name"]',
            '.employer-name', '.job-company', 'span.companyName'
        ]
<<<<<<< HEAD

=======
        
>>>>>>> update/main
        for selector in company_selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
<<<<<<< HEAD

=======
                
>>>>>>> update/main
        # Fallback to text pattern matching
        company_patterns = [
            r'Company:\s*([^\n]+)',
            r'Employer:\s*([^\n]+)',
            r'Organization:\s*([^\n]+)'
        ]
<<<<<<< HEAD

=======
        
>>>>>>> update/main
        for pattern in company_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
<<<<<<< HEAD

        return "Unknown"

=======
                
        return "Unknown"
        
>>>>>>> update/main
    def _extract_location(self, soup: BeautifulSoup, text: str) -> str:
        """Extract job location"""
        # Try structured selectors
        location_selectors = [
            '.location', '.job-location', '[data-testid="job-location"]',
            '.workplace-location', '.job-address'
        ]
<<<<<<< HEAD

=======
        
>>>>>>> update/main
        for selector in location_selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
<<<<<<< HEAD

=======
                
>>>>>>> update/main
        # Pattern matching for Kenyan locations
        kenyan_cities = ['Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Thika', 'Machakos']
        for city in kenyan_cities:
            if city.lower() in text.lower():
                return city
<<<<<<< HEAD

        return "Kenya"

=======
                
        return "Kenya"
        
>>>>>>> update/main
    def _extract_job_type(self, text: str) -> str:
        """Extract job type (Full-time, Part-time, Contract, etc.)"""
        job_types = {
            'full-time': ['full time', 'full-time', 'permanent', 'regular'],
            'part-time': ['part time', 'part-time'],
            'contract': ['contract', 'contractor', 'temporary', 'temp'],
            'internship': ['intern', 'internship', 'graduate program'],
            'remote': ['remote', 'work from home', 'wfh'],
            'freelance': ['freelance', 'consultant', 'independent']
        }
<<<<<<< HEAD

=======
        
>>>>>>> update/main
        text_lower = text.lower()
        for job_type, keywords in job_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return job_type.title()
<<<<<<< HEAD

        return "Full-time"  # Default

=======
                
        return "Full-time"  # Default
        
>>>>>>> update/main
    def _extract_experience_level(self, text: str) -> str:
        """Extract required experience level"""
        experience_patterns = [
            (r'(\d+)[\+\-\s]*years?\s+experience', 'experience'),
            (r'entry[\s\-]?level', 'Entry Level'),
            (r'junior', 'Junior'),
            (r'senior', 'Senior'),
            (r'lead', 'Lead'),
            (r'principal', 'Principal'),
            (r'manager', 'Manager'),
            (r'director', 'Director')
        ]
<<<<<<< HEAD

        text_lower = text.lower()

=======
        
        text_lower = text.lower()
        
>>>>>>> update/main
        # Check for specific year requirements
        years_match = re.search(r'(\d+)[\+\-\s]*years?\s+experience', text_lower)
        if years_match:
            years = int(years_match.group(1))
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
<<<<<<< HEAD

=======
                
>>>>>>> update/main
        # Check for level keywords
        for pattern, level in experience_patterns[1:]:
            if re.search(pattern, text_lower):
                return level
<<<<<<< HEAD

        return "Mid Level"  # Default

=======
                
        return "Mid Level"  # Default
        
>>>>>>> update/main
    def _extract_salary(self, soup: BeautifulSoup, text: str) -> Optional[Dict]:
        """Extract salary information"""
        # Try structured selectors
        salary_selectors = [
            '.salary', '.compensation', '.pay', '.salaryText'
        ]
<<<<<<< HEAD

=======
        
>>>>>>> update/main
        for selector in salary_selectors:
            elem = soup.select_one(selector)
            if elem:
                salary_text = elem.get_text(strip=True)
                return self._parse_salary(salary_text)
<<<<<<< HEAD

=======
                
>>>>>>> update/main
        # Pattern matching for salary
        salary_patterns = [
            r'salary:?\s*([^\n]+)',
            r'compensation:?\s*([^\n]+)',
            r'ksh\s*[\d,]+',
            r'kes\s*[\d,]+',
            r'\$\s*[\d,]+',
            r'[\d,]+\s*-\s*[\d,]+\s*(?:per|/)\s*(?:month|year)'
        ]
<<<<<<< HEAD

=======
        
>>>>>>> update/main
        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_salary(match.group(0))
<<<<<<< HEAD

        return None

=======
                
        return None
        
>>>>>>> update/main
    def _parse_salary(self, salary_text: str) -> Dict:
        """Parse salary text into structured format"""
        # Extract numbers
        numbers = re.findall(r'[\d,]+', salary_text.replace(',', ''))
        currency = 'KSH'
<<<<<<< HEAD

=======
        
>>>>>>> update/main
        if '$' in salary_text:
            currency = 'USD'
        elif 'kes' in salary_text.lower():
            currency = 'KES'
<<<<<<< HEAD

        period = 'month'
        if any(word in salary_text.lower() for word in ['year', 'annual', 'yearly']):
            period = 'year'

=======
            
        period = 'month'
        if any(word in salary_text.lower() for word in ['year', 'annual', 'yearly']):
            period = 'year'
            
>>>>>>> update/main
        if len(numbers) >= 2:
            return {
                'min': int(numbers[0]),
                'max': int(numbers[1]),
                'currency': currency,
                'period': period,
                'raw': salary_text
            }
        elif len(numbers) == 1:
            return {
                'amount': int(numbers[0]),
                'currency': currency,
                'period': period,
                'raw': salary_text
            }
<<<<<<< HEAD

        return {'raw': salary_text}

=======
            
        return {'raw': salary_text}
        
>>>>>>> update/main
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract job description"""
        description_selectors = [
            '.job-description', '.description', '.job-details',
            '.job-summary', '.overview', '.about-role'
        ]
<<<<<<< HEAD

=======
        
>>>>>>> update/main
        for selector in description_selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(separator=' ', strip=True)[:2000]
<<<<<<< HEAD

=======
                
>>>>>>> update/main
        # Fallback to main content
        main_content = soup.find('main') or soup.find('body')
        if main_content:
            return main_content.get_text(separator=' ', strip=True)[:2000]
<<<<<<< HEAD

        return ""

    def _extract_requirements(self, text: str) -> List[str]:
        """Extract job requirements"""
        requirements = []

=======
            
        return ""
        
    def _extract_requirements(self, text: str) -> List[str]:
        """Extract job requirements"""
        requirements = []
        
>>>>>>> update/main
        # Look for requirements sections
        req_sections = re.findall(
            r'(?:requirements?|qualifications?|must have|essential)[:\n](.*?)(?=\n[A-Z]|\n\n|$)',
            text, re.IGNORECASE | re.DOTALL
        )
<<<<<<< HEAD

=======
        
>>>>>>> update/main
        for section in req_sections:
            # Split by bullet points or line breaks
            items = re.split(r'[•\n]\s*', section.strip())
            for item in items:
                clean_item = item.strip()
                if len(clean_item) > 10 and len(clean_item) < 200:
                    requirements.append(clean_item)
<<<<<<< HEAD

        return requirements[:10]  # Limit to 10 requirements

=======
                    
        return requirements[:10]  # Limit to 10 requirements
        
>>>>>>> update/main
    def _extract_skills(self, text: str) -> List[str]:
        """Extract required skills"""
        # Common tech skills patterns
        skill_patterns = [
            r'\b(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|PHP|Ruby|Go|Rust|Swift|Kotlin)\b',
            r'\b(?:React|Angular|Vue|Django|Flask|Spring|Laravel|Rails|Express)\b',
            r'\b(?:AWS|Azure|GCP|Docker|Kubernetes|Jenkins|Git|Linux|Unix)\b',
            r'\b(?:SQL|MySQL|PostgreSQL|MongoDB|Redis|Elasticsearch)\b',
            r'\b(?:HTML|CSS|SASS|Bootstrap|Tailwind)\b',
            r'\b(?:Machine Learning|AI|Data Science|Analytics|Statistics)\b'
        ]
<<<<<<< HEAD

        skills = set()
        text_lower = text.lower()

        for pattern in skill_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            skills.update(matches)

=======
        
        skills = set()
        text_lower = text.lower()
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            skills.update(matches)
            
>>>>>>> update/main
        # Add soft skills
        soft_skills = ['communication', 'leadership', 'teamwork', 'problem solving', 'analytical']
        for skill in soft_skills:
            if skill in text_lower:
                skills.add(skill.title())
<<<<<<< HEAD

        return list(skills)[:15]  # Limit to 15 skills

=======
                
        return list(skills)[:15]  # Limit to 15 skills
        
>>>>>>> update/main
    def _extract_benefits(self, text: str) -> List[str]:
        """Extract job benefits"""
        benefits_keywords = [
            'health insurance', 'medical', 'dental', 'vision',
            'vacation', 'pto', 'paid time off', 'sick leave',
            'retirement', '401k', 'pension', 'bonus',
            'remote work', 'flexible hours', 'work from home',
            'training', 'professional development', 'certification',
            'gym', 'wellness', 'transport', 'parking'
        ]
<<<<<<< HEAD

        found_benefits = []
        text_lower = text.lower()

        for benefit in benefits_keywords:
            if benefit in text_lower:
                found_benefits.append(benefit.title())

        return found_benefits[:10]

=======
        
        found_benefits = []
        text_lower = text.lower()
        
        for benefit in benefits_keywords:
            if benefit in text_lower:
                found_benefits.append(benefit.title())
                
        return found_benefits[:10]
        
>>>>>>> update/main
    def _extract_deadline(self, soup: BeautifulSoup, text: str) -> Optional[str]:
        """Extract application deadline"""
        deadline_selectors = [
            '.deadline', '.closing-date', '.application-deadline'
        ]
<<<<<<< HEAD

=======
        
>>>>>>> update/main
        for selector in deadline_selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
<<<<<<< HEAD

=======
                
>>>>>>> update/main
        # Pattern matching
        deadline_patterns = [
            r'deadline:?\s*([^\n]+)',
            r'closing date:?\s*([^\n]+)',
            r'apply by:?\s*([^\n]+)'
        ]
<<<<<<< HEAD

=======
        
>>>>>>> update/main
        for pattern in deadline_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
<<<<<<< HEAD

        return None

=======
                
        return None
        
>>>>>>> update/main
    def _extract_education(self, text: str) -> List[str]:
        """Extract education requirements"""
        education_levels = [
            'Bachelor', 'Master', 'PhD', 'Doctorate', 'Degree',
            'Diploma', 'Certificate', 'Associate'
        ]
<<<<<<< HEAD

        found_education = []
        text_lower = text.lower()

        for level in education_levels:
            if level.lower() in text_lower:
                found_education.append(level)

        return found_education

=======
        
        found_education = []
        text_lower = text.lower()
        
        for level in education_levels:
            if level.lower() in text_lower:
                found_education.append(level)
                
        return found_education
        
>>>>>>> update/main
    def _extract_industry(self, text: str) -> str:
        """Extract industry/sector"""
        industries = {
            'Technology': ['software', 'tech', 'it', 'developer', 'engineer', 'programming'],
            'Finance': ['finance', 'banking', 'fintech', 'accounting', 'investment'],
            'Healthcare': ['health', 'medical', 'hospital', 'clinical', 'pharma'],
            'Education': ['education', 'teaching', 'university', 'academic', 'research'],
            'Marketing': ['marketing', 'advertising', 'digital marketing', 'seo', 'social media'],
            'Sales': ['sales', 'business development', 'account manager', 'customer success'],
            'Manufacturing': ['manufacturing', 'production', 'factory', 'industrial'],
            'Retail': ['retail', 'e-commerce', 'store', 'merchandise'],
            'Consulting': ['consulting', 'advisory', 'strategy', 'management consulting']
        }
<<<<<<< HEAD

        text_lower = text.lower()

        for industry, keywords in industries.items():
            if any(keyword in text_lower for keyword in keywords):
                return industry

        return "General"

    async def _enhance_with_ai(self, extracted_data: Dict, full_content: str) -> Dict:
        """Use AI to enhance and validate extracted information"""
        if not self.ai_client:
            logger.error(f"Error getting statistics: {e}")
            return {}
        finally:
            conn.close()

    def export_career_insights(self, output_file: str = "career_insights.json") -> bool:
        """Export career insights for the advising tool"""
        try:
            conn = sqlite3.connect(self.output_db_path)

            # Get comprehensive career data
            career_data = {
                'job_titles_by_industry': {},
                'skills_by_industry': {},
                'education_pathways': {},
                'salary_ranges_by_level': {},
                'career_progression_paths': {},
                'in_demand_skills': {},
                'certification_recommendations': {},
                'location_opportunities': {}
            }

            # Job titles by industry
            titles_by_industry = conn.execute("""
                                              SELECT jm.industry, jm.title_clean, COUNT(*) as frequency
                                              FROM jobs_meta jm
                                              WHERE jm.industry IS NOT NULL
                                                AND jm.title_clean IS NOT NULL
                                              GROUP BY jm.industry, jm.title_clean
                                              ORDER BY jm.industry, frequency DESC
                                              """).fetchall()

            for industry, title, freq in titles_by_industry:
                if industry not in career_data['job_titles_by_industry']:
                    career_data['job_titles_by_industry'][industry] = []
                career_data['job_titles_by_industry'][industry].append({
                    'title': title,
                    'frequency': freq
                })

            # Skills by industry
            skills_query = conn.execute("""
                                        SELECT jm.industry, st.technical_skills, st.programming_languages, st.frameworks
                                        FROM jobs_meta jm
                                                 JOIN skills_taxonomy st ON jm.job_id = st.job_id
                                        WHERE jm.industry IS NOT NULL
                                        """).fetchall()

            for industry, tech_skills, prog_langs, frameworks in skills_query:
                if industry not in career_data['skills_by_industry']:
                    career_data['skills_by_industry'][industry] = {
                        'technical_skills': [],
                        'programming_languages': [],
                        'frameworks': []
                    }

                # Parse JSON skills
                try:
                    if tech_skills:
                        career_data['skills_by_industry'][industry]['technical_skills'].extend(json.loads(tech_skills))
                    if prog_langs:
                        career_data['skills_by_industry'][industry]['programming_languages'].extend(
                            json.loads(prog_langs))
                    if frameworks:
                        career_data['skills_by_industry'][industry]['frameworks'].extend(json.loads(frameworks))
                except json.JSONDecodeError:
                    continue

            # Education pathways
            edu_pathways = conn.execute("""
                                        SELECT er.level, er.field, jm.industry, COUNT(*) as frequency
                                        FROM education_requirements er
                                                 JOIN jobs_meta jm ON er.job_id = jm.job_id
                                        WHERE er.field IS NOT NULL
                                          AND jm.industry IS NOT NULL
                                        GROUP BY er.level, er.field, jm.industry
                                        ORDER BY frequency DESC
                                        """).fetchall()

            for level, field, industry, freq in edu_pathways:
                pathway_key = f"{level}_{field}"
                if pathway_key not in career_data['education_pathways']:
                    career_data['education_pathways'][pathway_key] = {
                        'education_level': level,
                        'field_of_study': field,
                        'industries': []
                    }
                career_data['education_pathways'][pathway_key]['industries'].append({
                    'industry': industry,
                    'job_count': freq
                })

            # Salary ranges by level
            salary_by_level = conn.execute("""
                                           SELECT jc.level,
                                                  AVG(c.salary_min) as avg_min,
                                                  AVG(c.salary_max) as avg_max,
                                                  COUNT(*) as count
                                           FROM job_classification jc
                                               JOIN compensation c
                                           ON jc.job_id = c.job_id
                                           WHERE jc.level IS NOT NULL
                                             AND (c.salary_min IS NOT NULL
                                              OR c.salary_max IS NOT NULL)
                                           GROUP BY jc.level
                                           """).fetchall()

            for level, avg_min, avg_max, count in salary_by_level:
                career_data['salary_ranges_by_level'][level] = {
                    'average_min_salary': round(avg_min, 2) if avg_min else None,
                    'average_max_salary': round(avg_max, 2) if avg_max else None,
                    'sample_size': count
                }

            # Career progression paths
            progression_data = conn.execute("""
                                            SELECT entry_level, mid_level, senior_level, COUNT(*) as frequency
                                            FROM career_progression
                                            WHERE entry_level IS NOT NULL
                                               OR mid_level IS NOT NULL
                                               OR senior_level IS NOT NULL
                                            GROUP BY entry_level, mid_level, senior_level
                                            ORDER BY frequency DESC
                                            """).fetchall()

            for entry, mid, senior, freq in progression_data:
                if any([entry, mid, senior]):
                    path_key = f"{entry or 'Unknown'}_to_{senior or 'Unknown'}"
                    career_data['career_progression_paths'][path_key] = {
                        'entry_level': entry,
                        'mid_level': mid,
                        'senior_level': senior,
                        'frequency': freq
                    }

            # In-demand skills (most frequently mentioned)
            all_skills = []
            skills_data = conn.execute("""
                                       SELECT technical_skills, programming_languages, frameworks
                                       FROM skills_taxonomy
                                       """).fetchall()

            for tech_skills, prog_langs, frameworks in skills_data:
                try:
                    if tech_skills:
                        all_skills.extend(json.loads(tech_skills))
                    if prog_langs:
                        all_skills.extend(json.loads(prog_langs))
                    if frameworks:
                        all_skills.extend(json.loads(frameworks))
                except json.JSONDecodeError:
                    continue

            # Count skill frequencies
            from collections import Counter
            skill_counts = Counter(all_skills)
            career_data['in_demand_skills'] = dict(skill_counts.most_common(50))

            # Certification recommendations
            cert_data = conn.execute("""
                                     SELECT c.name,
                                            c.issuer,
                                            COUNT(*)                                        as frequency,
                                            AVG(CASE WHEN c.required = 1 THEN 1 ELSE 0 END) as required_ratio
                                     FROM certifications c
                                     WHERE c.name IS NOT NULL
                                     GROUP BY c.name, c.issuer
                                     ORDER BY frequency DESC LIMIT 20
                                     """).fetchall()

            for name, issuer, freq, req_ratio in cert_data:
                career_data['certification_recommendations'][name] = {
                    'issuer': issuer,
                    'frequency': freq,
                    'often_required': req_ratio > 0.5
                }

            # Location opportunities
            location_data = conn.execute("""
                                         SELECT lw.office_location,
                                                COUNT(*)          as job_count,
                                                AVG(c.salary_min) as avg_salary_min,
                                                AVG(c.salary_max) as avg_salary_max
                                         FROM location_work lw
                                                  LEFT JOIN compensation c ON lw.job_id = c.job_id
                                         WHERE lw.office_location IS NOT NULL
                                         GROUP BY lw.office_location
                                         ORDER BY job_count DESC LIMIT 30
                                         """).fetchall()

            for location, job_count, avg_min, avg_max in location_data:
                career_data['location_opportunities'][location] = {
                    'job_count': job_count,
                    'average_salary_min': round(avg_min, 2) if avg_min else None,
                    'average_salary_max': round(avg_max, 2) if avg_max else None
                }

            # Add metadata
            career_data['metadata'] = {
                'generated_at': datetime.now().isoformat(),
                'total_jobs_analyzed': conn.execute("SELECT COUNT(*) FROM jobs_meta").fetchone()[0],
                'data_sources': ['job_postings'],
                'version': '1.0'
            }

            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(career_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Career insights exported to {output_file}")
            return True


        try:
            # Prepare content for AI analysis
            content_summary = full_content[:3000]  # Limit content length

=======
        
        text_lower = text.lower()
        
        for industry, keywords in industries.items():
            if any(keyword in text_lower for keyword in keywords):
                return industry
                
        return "General"
        
    async def _enhance_with_ai(self, extracted_data: Dict, full_content: str) -> Dict:
        """Use AI to enhance and validate extracted information"""
        if not self.ai_client:
            return {}
            
        try:
            # Prepare content for AI analysis
            content_summary = full_content[:3000]  # Limit content length
            
>>>>>>> update/main
            prompt = f"""
            Analyze this job posting and extract/enhance the following information:
            
            Job Title: {extracted_data.get('title', 'Unknown')}
            Company: {extracted_data.get('company', 'Unknown')}
            
            Content: {content_summary}
            
            Please provide a JSON response with:
            1. skills_analysis: Most important skills required (list of 5-10 skills)
            2. experience_summary: Brief summary of experience requirements
            3. role_level: Entry/Junior/Mid/Senior/Executive
            4. remote_friendly: true/false based on remote work mentions
            5. growth_potential: Low/Medium/High career growth potential
            6. industry_category: Primary industry category
            7. key_responsibilities: Top 3-5 main responsibilities
            
            Return only valid JSON.
            """
<<<<<<< HEAD

            response = await self.ai_client.chat([UserMessage(content=prompt)])

=======
            
            response = await self.ai_client.chat([UserMessage(content=prompt)])
            
>>>>>>> update/main
            # Parse AI response
            try:
                ai_data = json.loads(response.content)
                return ai_data
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI response as JSON")
                return {}
<<<<<<< HEAD

        except Exception as e:
            logger.error(f"Error in AI enhancement: {e}")
            return {}

=======
                
        except Exception as e:
            logger.error(f"Error in AI enhancement: {e}")
            return {}
            
>>>>>>> update/main
    def _create_processed_record(self, original_record: Dict, extracted_data: Dict, ai_data: Dict) -> Dict:
        """Create final processed job record"""
        processed_record = {
            # Original data
            'id': original_record['id'],
            'source': original_record['source'],
            'scraped_at': original_record['scraped_at'],
            'link': original_record['link'],
<<<<<<< HEAD

=======
            
>>>>>>> update/main
            # Processed data
            'title': extracted_data.get('title', original_record.get('title', '')),
            'company': extracted_data.get('company', 'Unknown'),
            'location': extracted_data.get('location', 'Kenya'),
            'job_type': extracted_data.get('job_type', 'Full-time'),
            'experience_level': extracted_data.get('experience_level', 'Mid Level'),
            'salary': extracted_data.get('salary'),
            'description': extracted_data.get('description', ''),
            'requirements': extracted_data.get('requirements', []),
            'skills': extracted_data.get('skills', []),
            'benefits': extracted_data.get('benefits', []),
            'deadline': extracted_data.get('deadline'),
            'education': extracted_data.get('education', []),
            'industry': extracted_data.get('industry', 'General'),
<<<<<<< HEAD

=======
            
>>>>>>> update/main
            # AI-enhanced data
            'ai_skills_analysis': ai_data.get('skills_analysis', []),
            'ai_experience_summary': ai_data.get('experience_summary', ''),
            'ai_role_level': ai_data.get('role_level', ''),
            'remote_friendly': ai_data.get('remote_friendly', False),
            'growth_potential': ai_data.get('growth_potential', 'Medium'),
            'ai_industry_category': ai_data.get('industry_category', ''),
            'key_responsibilities': ai_data.get('key_responsibilities', []),
<<<<<<< HEAD

=======
            
>>>>>>> update/main
            # Metadata
            'processed': True,
            'processed_at': datetime.utcnow(),
            'quality_score': self._calculate_quality_score(extracted_data, ai_data)
        }
<<<<<<< HEAD

        return processed_record

    def _calculate_quality_score(self, extracted_data: Dict, ai_data: Dict) -> float:
        """Calculate quality score for processed job (0-1)"""
        score = 0.0

=======
        
        return processed_record
        
    def _calculate_quality_score(self, extracted_data: Dict, ai_data: Dict) -> float:
        """Calculate quality score for processed job (0-1)"""
        score = 0.0
        
>>>>>>> update/main
        # Check completeness of key fields
        if extracted_data.get('title'): score += 0.2
        if extracted_data.get('company') and extracted_data['company'] != 'Unknown': score += 0.1
        if extracted_data.get('description'): score += 0.2
        if extracted_data.get('skills'): score += 0.1
        if extracted_data.get('requirements'): score += 0.1
        if extracted_data.get('salary'): score += 0.1
        if ai_data.get('skills_analysis'): score += 0.1
        if ai_data.get('key_responsibilities'): score += 0.1
<<<<<<< HEAD

        return min(1.0, score)

=======
        
        return min(1.0, score)
        
>>>>>>> update/main
    def _create_failed_record(self, original_record: Dict, error_message: str) -> Dict:
        """Create record for failed processing"""
        return {
            'id': original_record['id'],
            'source': original_record['source'],
            'scraped_at': original_record['scraped_at'],
            'link': original_record['link'],
            'title': original_record.get('title', 'Unknown'),
            'processed': False,
            'processing_failed': True,
            'error_message': error_message,
            'processed_at': datetime.utcnow(),
            'quality_score': 0.0
        }
<<<<<<< HEAD
            logger.error(f"Error exporting career insights: {e}")
            return False
        finally:
            conn.close()

    def cleanup_failed_jobs(self) -> int:
        """Clean up jobs that have repeatedly failed processing"""
        conn = sqlite3.connect(self.output_db_path)

        try:
            # Delete jobs that have failed more than max_retries times
            cursor = conn.execute("""
                                  DELETE
                                  FROM processing_status
                                  WHERE status = 'error'
                                    AND retry_count > ?
                                  """, (self.max_retries,))

            deleted_count = cursor.rowcount
            conn.commit()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} failed job records")

            return deleted_count

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0
        finally:
            conn.close()

    def validate_database_integrity(self) -> Dict[str, Any]:
        """Validate the integrity of the processed data"""
        conn = sqlite3.connect(self.output_db_path)

        try:
            validation_results = {
                'issues': [],
                'warnings': [],
                'summary': {}
            }

            # Check for orphaned records
            orphaned_checks = [
                ("job_classification", "jobs_meta"),
                ("location_work", "jobs_meta"),
                ("skills_taxonomy", "jobs_meta"),
                ("certifications", "jobs_meta"),
                ("career_progression", "jobs_meta"),
                ("compensation", "jobs_meta"),
                ("education_requirements", "jobs_meta")
            ]

            for child_table, parent_table in orphaned_checks:
                orphaned = conn.execute(f"""
                    SELECT COUNT(*) FROM {child_table} c
                    LEFT JOIN {parent_table} p ON c.job_id = p.job_id
                    WHERE p.job_id IS NULL
                """).fetchone()[0]

                if orphaned > 0:
                    validation_results['issues'].append(f"Found {orphaned} orphaned records in {child_table}")

            # Check for missing critical data
            missing_titles = \
            conn.execute("SELECT COUNT(*) FROM jobs_meta WHERE title_clean IS NULL OR title_clean = ''").fetchone()[0]
            if missing_titles > 0:
                validation_results['warnings'].append(f"{missing_titles} jobs missing clean titles")

            missing_companies = \
            conn.execute("SELECT COUNT(*) FROM jobs_meta WHERE company IS NULL OR company = ''").fetchone()[0]
            if missing_companies > 0:
                validation_results['warnings'].append(f"{missing_companies} jobs missing company information")

            # Check data quality scores
            low_confidence_edu = \
            conn.execute("SELECT COUNT(*) FROM education_requirements WHERE confidence_score < 0.5").fetchone()[0]
            if low_confidence_edu > 0:
                validation_results['warnings'].append(
                    f"{low_confidence_edu} education requirements with low confidence scores")

            # Summary statistics
            validation_results['summary'] = {
                'total_jobs': conn.execute("SELECT COUNT(*) FROM jobs_meta").fetchone()[0],
                'total_education_requirements': conn.execute("SELECT COUNT(*) FROM education_requirements").fetchone()[
                    0],
                'total_certifications': conn.execute("SELECT COUNT(*) FROM certifications").fetchone()[0],
                'jobs_with_salary_info': conn.execute(
                    "SELECT COUNT(*) FROM compensation WHERE salary_min IS NOT NULL OR salary_max IS NOT NULL").fetchone()[
                    0]
            }

            return validation_results

        except Exception as e:
            logger.error(f"Error during validation: {e}")
            return {'error': str(e)}
        finally:
            conn.close()


def main():
    """Main function to run the processing pipeline"""
    try:
        # Initialize processor
        processor = AcademicDetailsProcessor(
            input_db_path="db/jobs.sqlite3",
            output_db_path="db/processed_jobs.sqlite3",
            batch_size=10,
            max_retries=3
        )

        logger.info("Starting job processing pipeline...")

        # Run synchronous batch processing
        results = processor.batch_extract()

        # Get and log statistics
        stats = processor.get_processing_statistics()
        logger.info(f"Processing complete. Statistics: {stats}")

        # Export career insights
        success = processor.export_career_insights("career_insights.json")
        if success:
            logger.info("Career insights exported successfully")

        # Validate data integrity
        validation = processor.validate_database_integrity()
        if validation.get('issues'):
            logger.warning(f"Data integrity issues found: {validation['issues']}")

        # Cleanup failed jobs
        cleaned = processor.cleanup_failed_jobs()
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} failed job records")

        logger.info("Pipeline execution completed successfully")

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise


async def main_async():
    """Async version of main function"""
    try:
        processor = AcademicDetailsProcessor(
            input_db_path="db/jobs.sqlite3",
            output_db_path="db/processed_jobs.sqlite3",
            batch_size=10,
            max_retries=3
        )

        logger.info("Starting async job processing pipeline...")

        # Run asynchronous batch processing
        results = await processor.batch_extract_async(max_concurrent=5)

        # Get and log statistics
        stats = processor.get_processing_statistics()
        logger.info(f"Async processing complete. Statistics: {stats}")

        # Export career insights
        success = processor.export_career_insights("career_insights_async.json")
        if success:
            logger.info("Career insights exported successfully")

        logger.info("Async pipeline execution completed successfully")

    except Exception as e:
        logger.error(f"Async pipeline execution failed: {e}")
        raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--async":
        asyncio.run(main_async())
    else:
        main()
=======


>>>>>>> update/main
# Convenience function for processing batches
async def process_job_batch(job_records: List[Dict], batch_size: int = 5) -> List[Dict]:
    """
    Process a batch of job records
    """
    processed_jobs = []
<<<<<<< HEAD

=======
    
>>>>>>> update/main
    async with JobProcessor() as processor:
        # Process jobs in smaller batches to avoid overwhelming servers
        for i in range(0, len(job_records), batch_size):
            batch = job_records[i:i + batch_size]
<<<<<<< HEAD

            # Process batch concurrently
            tasks = [processor.process_job(job) for job in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

=======
            
            # Process batch concurrently
            tasks = [processor.process_job(job) for job in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
>>>>>>> update/main
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch processing error: {result}")
                else:
                    processed_jobs.append(result)
<<<<<<< HEAD

            # Small delay between batches
            if i + batch_size < len(job_records):
                await asyncio.sleep(2)

=======
                    
            # Small delay between batches
            if i + batch_size < len(job_records):
                await asyncio.sleep(2)
                
>>>>>>> update/main
    return processed_jobs