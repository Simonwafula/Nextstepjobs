import os
import re
import sqlite3
import logging
import asyncio
from typing import List, Optional, Literal

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableSequence
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Regex patterns for abbreviation normalization
BS_RE = re.compile(r"\bB\.S\.\b", re.IGNORECASE)
BA_RE = re.compile(r"\bB\.A\.\b", re.IGNORECASE)
MS_RE = re.compile(r"\bM\.S\.\b", re.IGNORECASE)
MA_RE = re.compile(r"\bM\.A\.\b", re.IGNORECASE)
PHD_RE = re.compile(r"\bPh\.D\.\b", re.IGNORECASE)
WHITESPACE_RE = re.compile(r"\s+\n?")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data models with defaults to handle missing fields
class JobClassification(BaseModel):
    category: Optional[str] = None
    level: Optional[str] = None
    function: Optional[str] = None

class LocationWork(BaseModel):
    office_location: Optional[str] = None
    remote: Optional[bool] = None
    onsite: Optional[bool] = None

class SkillsTaxonomy(BaseModel):
    main_skill: Optional[str] = None
    specific_skills: List[str] = Field(default_factory=list)
    desirable_skills: List[str] = Field(default_factory=list)

class Certification(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    year: Optional[int] = None

class CareerProgression(BaseModel):
    entry_level: Optional[str] = None
    mid_level: Optional[str] = None
    senior_level: Optional[str] = None

class CompensationBenefits(BaseModel):
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    benefits: List[str] = Field(default_factory=list)

class JobExtraction(BaseModel):
    # Basic fields
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

    # Nested structures with defaults
    job_classification: JobClassification = Field(default_factory=JobClassification)
    location_and_work: LocationWork = Field(default_factory=LocationWork)
    skills: SkillsTaxonomy = Field(default_factory=SkillsTaxonomy)
    certifications: List[Certification] = Field(default_factory=list)
    career_progression: CareerProgression = Field(default_factory=CareerProgression)
    compensation: CompensationBenefits = Field(default_factory=CompensationBenefits)

    raw_text_analyzed: str = Field(default="")

class AcademicDetailsProcessor:
    def __init__(
        self,
        input_db_path: str = "db/jobs.sqlite3",
        output_db_path: str = "db/processed_jobs.sqlite3",
        llm_model: str = "gpt-4o-mini",
        temperature: float = 0.1,
        api_key: Optional[str] = None
    ):
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OpenAI API key must be set via parameter or env var")
        self.llm = OpenAI(model=llm_model, temperature=temperature, openai_api_key=key)
        self.parser = PydanticOutputParser(pydantic_object=JobExtraction)
        self.chain: RunnableSequence = self._create_chain()

        self.input_db_path = input_db_path
        self.output_db_path = output_db_path
        self._setup_db()

    def _setup_db(self):
        conn = sqlite3.connect(self.output_db_path)
        # metadata table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs_meta (
                job_id INTEGER PRIMARY KEY,
                full_link TEXT,
                title_clean TEXT,
                company TEXT,
                company_location TEXT,
                post_date TEXT,
                industry TEXT,
                job_type TEXT,
                job_category TEXT,
                job_description TEXT,
                application_deadline TEXT,
                additional_requirements TEXT
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_meta_job ON jobs_meta(job_id);")
        # nested tables
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS job_classification (
                job_id INTEGER PRIMARY KEY,
                category TEXT,
                level TEXT,
                function TEXT,
                FOREIGN KEY(job_id) REFERENCES jobs_meta(job_id)
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS location_work (
                job_id INTEGER PRIMARY KEY,
                office_location TEXT,
                remote BOOLEAN,
                onsite BOOLEAN,
                FOREIGN KEY(job_id) REFERENCES jobs_meta(job_id)
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS skills_taxonomy (
                job_id INTEGER PRIMARY KEY,
                main_skill TEXT,
                specific_skills TEXT,
                desirable_skills TEXT,
                FOREIGN KEY(job_id) REFERENCES jobs_meta(job_id)
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS certifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                name TEXT,
                issuer TEXT,
                year INTEGER,
                FOREIGN KEY(job_id) REFERENCES jobs_meta(job_id)
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS career_progression (
                job_id INTEGER PRIMARY KEY,
                entry_level TEXT,
                mid_level TEXT,
                senior_level TEXT,
                FOREIGN KEY(job_id) REFERENCES jobs_meta(job_id)
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS compensation (
                job_id INTEGER PRIMARY KEY,
                salary_min REAL,
                salary_max REAL,
                benefits TEXT,
                FOREIGN KEY(job_id) REFERENCES jobs_meta(job_id)
            );
            """
        )
        conn.commit()
        conn.close()

    def _create_chain(self) -> RunnableSequence:
        prompt = PromptTemplate.from_template(
            "Extract the following from the job posting text:\n"
            "- Full link, clean title, company, company location, post date (YYYY-MM-DD)\n"
            "- Industry, job type, category, description, application deadline, additional requirements\n"
            "- Nested: job_classification, location_and_work, skills (main & specific & desirable), certifications, career_progression, compensation\n\n"
            "TEXT:\n{text}\n\n{format_instructions}"
        )
        return prompt | self.llm | self.parser

    def _preprocess_text(self, text: str) -> str:
        t = WHITESPACE_RE.sub(" ", text)
        for rex, sub in [(BS_RE, "Bachelor"), (BA_RE, "Bachelor"), (MS_RE, "Master"), (MA_RE, "Master"), (PHD_RE, "PhD")]:
            t = rex.sub(sub, t)
        return t.strip()

    def extract_and_store(self, job_id: int, full_link: str, content: str) -> JobExtraction:
        processed = self._preprocess_text(content)
        try:
            data: JobExtraction = self.chain.invoke({
                "text": processed,
                "format_instructions": self.parser.get_format_instructions()
            })
            data.raw_text_analyzed = content[:500]
            logger.info(f"Job {job_id}: extracted fields")
            conn = sqlite3.connect(self.output_db_path)
            try:
                conn.execute("BEGIN")
                # metadata
                conn.execute(
                    "INSERT OR REPLACE INTO jobs_meta VALUES (?,?,?,?,?,?,?,?,?,?,?,?);",
                    (job_id, full_link, data.title_clean, data.company, data.company_location,
                     data.post_date, data.industry, data.job_type, data.job_category,
                     data.job_description, data.application_deadline, data.additional_requirements)
                )
                # classification
                conn.execute(
                    "INSERT OR REPLACE INTO job_classification VALUES (?,?,?,?);",
                    (job_id, data.job_classification.category, data.job_classification.level, data.job_classification.function)
                )
                # location work
                conn.execute(
                    "INSERT OR REPLACE INTO location_work VALUES (?,?,?,?);",
                    (job_id, data.location_and_work.office_location, data.location_and_work.remote, data.location_and_work.onsite)
                )
                # skills taxonomy
                import json
                conn.execute(
                    "INSERT OR REPLACE INTO skills_taxonomy VALUES (?,?,?,?);",
                    (job_id, data.skills.main_skill, json.dumps(data.skills.specific_skills), json.dumps(data.skills.desirable_skills))
                )
                # certifications
                for cert in data.certifications:
                    conn.execute(
                        "INSERT INTO certifications (job_id,name,issuer,year) VALUES (?,?,?,?);",
                        (job_id, cert.name, cert.issuer, cert.year)
                    )
                # career progression
                conn.execute(
                    "INSERT OR REPLACE INTO career_progression VALUES (?,?,?,?);",
                    (job_id, data.career_progression.entry_level, data.career_progression.mid_level, data.career_progression.senior_level)
                )
                # compensation
                conn.execute(
                    "INSERT OR REPLACE INTO compensation VALUES (?,?,?,?);",
                    (job_id, data.compensation.salary_min, data.compensation.salary_max, json.dumps(data.compensation.benefits))
                )
                conn.commit()
            except Exception as db_e:
                conn.rollback()
                logger.error(f"Job {job_id}: DB failed: {db_e}")
                raise
            finally:
                conn.close()
            return data
        except Exception as e:
            logger.error(f"Job {job_id}: extraction failed: {e}")
            return JobExtraction(raw_text_analyzed=content)

    def batch_extract(self) -> List[JobExtraction]:
        conn = sqlite3.connect(self.input_db_path)
        rows = conn.execute("SELECT id, full_link, content FROM jobs_data").fetchall()
        conn.close()
        return [self.extract_and_store(jid, link, txt) for jid, link, txt in rows]

    async def batch_extract_async(self) -> List[JobExtraction]:
        conn = sqlite3.connect(self.input_db_path)
        rows = conn.execute("SELECT id, full_link, content FROM jobs_data").fetchall()
        conn.close()
        tasks = [self.extract_and_store(jid, link, txt) for jid, link, txt in rows]
        return await asyncio.gather(*tasks)

if __name__ == "__main__":
    processor = AcademicDetailsProcessor()
    processor.batch_extract()
    # async_results = asyncio.run(processor.batch_extract_async())
