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

# Envt Loading
load_dotenv()

# Precompile regex patterns for abbreviation normalization
BS_RE = re.compile(r"\bB\.S\.\b", re.IGNORECASE)
BA_RE = re.compile(r"\bB\.A\.\b", re.IGNORECASE)
MS_RE = re.compile(r"\bM\.S\.\b", re.IGNORECASE)
MA_RE = re.compile(r"\bM\.A\.\b", re.IGNORECASE)
PHD_RE = re.compile(r"\bPh\.D\.\b", re.IGNORECASE)
WHITESPACE_RE = re.compile(r"\s+\n?")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EducationRequirement(BaseModel):
    """Model for a single education requirement"""
    level: Literal[
        "high_school", "certificate", "diploma", "associate",
        "bachelor", "master", "phd", "professional_license",
        "none_specified", "equivalent_experience"
    ] = Field(description="The specific education level required")

    field: Optional[str] = Field(
        None,
        description="The specific field of study"
    )

    requirement_type: Literal["required", "preferred", "equivalent_experience_accepted"] = Field(
        description="Whether this education is required, preferred, or if equivalent experience is accepted"
    )

    years_experience_substitute: Optional[int] = Field(
        None,
        description="Years of experience that can substitute for this education"
    )

    confidence_score: float = Field(
        description="Confidence score for this extraction (0.0 to 1.0)"
    )

class EducationExtraction(BaseModel):
    """Container for all education requirements extracted from a job posting"""
    requirements: List[EducationRequirement] = Field(
        ..., description="List of all education requirements found"
    )
    raw_text_analyzed: str = Field(
        ..., description="The original text that was analyzed"
    )

class AcademicDetailsProcessor:
    """
    Processor for extracting and storing academic requirements from job postings
    """
    def __init__(
        self,
        input_db_path: str = "db/jobs.sqlite3",
        output_db_path: str = "db/processed_education_jobs.sqlite3",
        llm_model: str = "gpt-4o-mini",
        temperature: float = 0.1,
        api_key: Optional[str] = None
    ):
        # Determine API key
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OpenAI API key must be set via parameter or env var")

        # Initialize LLM and parser
        self.llm = OpenAI(
            model=llm_model,
            temperature=temperature,
            api_key=key
        )
        self.output_parser = PydanticOutputParser(pydantic_object=EducationExtraction)
        self.chain: RunnableSequence = self._create_extraction_chain()

        self.input_db_path = input_db_path
        self.output_db_path = output_db_path
        self._setup_output_database()

    def _setup_output_database(self):
        """Initialize SQLite tables for storing requirements"""
        conn = sqlite3.connect(self.output_db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS education_requirements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                level TEXT NOT NULL,
                field TEXT,
                requirement_type TEXT NOT NULL,
                years_experience_substitute INTEGER,
                confidence_score REAL NOT NULL,
                FOREIGN KEY(job_id) REFERENCES jobs(id)
            )
            """
        )
        conn.commit()
        conn.close()

    def _create_extraction_chain(self) -> RunnableSequence:
        """Build the runnable sequence: prompt | llm | parser"""
        prompt = PromptTemplate.from_template(
            "Extract education requirements from the following job text:\n\n{text}\n\n{format_instructions}"
        )
        return prompt | self.llm | self.output_parser

    def _preprocess_text(self, text: str) -> str:
        """Clean whitespace and normalize abbreviations"""
        text = WHITESPACE_RE.sub(" ", text)
        text = BS_RE.sub("Bachelor", text)
        text = BA_RE.sub("Bachelor", text)
        text = MS_RE.sub("Master", text)
        text = MA_RE.sub("Master", text)
        text = PHD_RE.sub("PhD", text)
        return text.strip()

    def _post_process_results(self, extraction: EducationExtraction) -> EducationExtraction:
        """Clamp confidence and normalize field case"""
        for req in extraction.requirements:
            req.confidence_score = min(max(req.confidence_score, 0.0), 1.0)
            if req.field:
                req.field = req.field.lower().strip()
        return extraction

    def extract_and_store(self, job_id: int, job_content: str) -> EducationExtraction:
        """Extract requirements for a single job and store into DB"""
        processed = self._preprocess_text(job_content)
        result: EducationExtraction = self.chain.invoke({
            "text": processed,
            "format_instructions": self.output_parser.get_format_instructions()
        })
        result = self._post_process_results(result)
        logger.info(f"Job {job_id}: extracted {len(result.requirements)} requirements")

        conn = sqlite3.connect(self.output_db_path)
        for req in result.requirements:
            conn.execute(
                "INSERT INTO education_requirements "
                "(job_id, level, field, requirement_type, years_experience_substitute, confidence_score) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    job_id,
                    req.level,
                    req.field,
                    req.requirement_type,
                    req.years_experience_substitute,
                    req.confidence_score
                )
            )
        conn.commit()
        conn.close()

        return result

    def batch_extract(self) -> List[EducationExtraction]:
        """Extract from all postings in the input database"""
        conn_in = sqlite3.connect(self.input_db_path)
        cursor = conn_in.execute("SELECT id, content FROM jobs_data")
        rows = cursor.fetchall()
        conn_in.close()

        results: List[EducationExtraction] = []
        conn_out = sqlite3.connect(self.output_db_path)
        for job_id, text in rows:
            try:
                res = self.extract_and_store(job_id, text)
                results.append(res)
            except Exception as e:
                logger.error(f"Error processing job {job_id}: {e}")
                results.append(EducationExtraction(requirements=[], raw_text_analyzed=text))
        conn_out.close()
        return results

if __name__ == "__main__":
    processor = AcademicDetailsProcessor()
    all_results = processor.batch_extract()
    for res in all_results:
        print(res.model_dump_json(indent=2))
