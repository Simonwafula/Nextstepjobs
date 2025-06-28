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

# Load environment
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
    level: Literal[
        "high_school", "certificate", "diploma", "associate",
        "bachelor", "master", "phd", "professional_license",
        "none_specified", "equivalent_experience"
    ]
    field: Optional[str]
    requirement_type: Literal["required", "preferred", "equivalent_experience_accepted"]
    years_experience_substitute: Optional[int]
    confidence_score: float

class EducationExtraction(BaseModel):
    requirements: List[EducationRequirement]
    raw_text_analyzed: str

class AcademicDetailsProcessor:
    def __init__(
        self,
        input_db_path: str = "db/jobs.sqlite3",
        output_db_path: str = "db/processed_education_jobs.sqlite3",
        llm_model: str = "gpt-4o-mini",
        temperature: float = 0.1,
        api_key: Optional[str] = None
    ):
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OpenAI API key must be set via parameter or env var")

        self.llm = OpenAI(model=llm_model, temperature=temperature, openai_api_key=key)
        self.output_parser = PydanticOutputParser(pydantic_object=EducationExtraction)
        self.chain: RunnableSequence = self._create_extraction_chain()

        self.input_db_path = input_db_path
        self.output_db_path = output_db_path
        self._setup_output_database()

    def _setup_output_database(self):
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
                FOREIGN KEY(job_id) REFERENCES jobs_data(id)
            );
            """
        )
        # index for faster lookups
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_edu_job ON education_requirements(job_id);"
        )
        conn.commit()
        conn.close()

    def _create_extraction_chain(self) -> RunnableSequence:
        prompt = PromptTemplate.from_template(
            "Extract education requirements from the following job text:\n\n{text}\n\n{format_instructions}"
        )
        return prompt | self.llm | self.output_parser

    def _preprocess_text(self, text: str) -> str:
        text = WHITESPACE_RE.sub(" ", text)
        text = BS_RE.sub("Bachelor", text)
        text = BA_RE.sub("Bachelor", text)
        text = MS_RE.sub("Master", text)
        text = MA_RE.sub("Master", text)
        text = PHD_RE.sub("PhD", text)
        return text.strip()

    def _post_process_results(self, extraction: EducationExtraction) -> EducationExtraction:
        for req in extraction.requirements:
            req.confidence_score = min(max(req.confidence_score, 0.0), 1.0)
            if req.field:
                req.field = req.field.lower().strip()
        return extraction

    def extract_and_store(self, job_id: int, job_content: str) -> EducationExtraction:
        processed = self._preprocess_text(job_content)
        try:
            result: EducationExtraction = self.chain.invoke({
                "text": processed,
                "format_instructions": self.output_parser.get_format_instructions()
            })
            result = self._post_process_results(result)
            logger.info(f"Job {job_id}: extracted {len(result.requirements)} requirements")

            conn = sqlite3.connect(self.output_db_path)
            try:
                conn.execute("BEGIN")
                for req in result.requirements:
                    conn.execute(
                        "INSERT INTO education_requirements (job_id, level, field, requirement_type, years_experience_substitute, confidence_score) VALUES (?, ?, ?, ?, ?, ?)",
                        (job_id, req.level, req.field, req.requirement_type,
                         req.years_experience_substitute, req.confidence_score)
                    )
                conn.commit()
            except Exception as db_e:
                conn.rollback()
                logger.error(f"Job {job_id}: DB transaction failed: {db_e}")
                raise
            finally:
                conn.close()

            return result

        except Exception as e:
            logger.error(f"Job {job_id}: extraction failed: {e}. Text snippet: {job_content[:200]!r}")
            return EducationExtraction(requirements=[], raw_text_analyzed=job_content)

    def batch_extract(self) -> List[EducationExtraction]:
        conn = sqlite3.connect(self.input_db_path)
        rows = conn.execute("SELECT id, content FROM jobs_data").fetchall()
        conn.close()

        results: List[EducationExtraction] = []
        for job_id, text in rows:
            results.append(self.extract_and_store(job_id, text))
        return results

    async def extract_and_store_async(self, job_id: int, job_content: str) -> EducationExtraction:
        processed = self._preprocess_text(job_content)
        try:
            result: EducationExtraction = await self.chain.ainvoke({
                "text": processed,
                "format_instructions": self.output_parser.get_format_instructions()
            })
            result = self._post_process_results(result)
            logger.info(f"[async] Job {job_id}: extracted {len(result.requirements)} requirements")

            conn = sqlite3.connect(self.output_db_path)
            try:
                conn.execute("BEGIN")
                for req in result.requirements:
                    conn.execute(
                        "INSERT INTO education_requirements (job_id, level, field, requirement_type, years_experience_substitute, confidence_score) VALUES (?, ?, ?, ?, ?, ?)",
                        (job_id, req.level, req.field, req.requirement_type,
                         req.years_experience_substitute, req.confidence_score)
                    )
                conn.commit()
            except Exception as db_e:
                conn.rollback()
                logger.error(f"[async] Job {job_id}: DB transaction failed: {db_e}")
                raise
            finally:
                conn.close()

            return result
        except Exception as e:
            logger.error(f"[async] Job {job_id}: extraction failed: {e}")
            return EducationExtraction(requirements=[], raw_text_analyzed=job_content)

    async def batch_extract_async(self) -> List[EducationExtraction]:
        conn = sqlite3.connect(self.input_db_path)
        rows = conn.execute("SELECT id, content FROM jobs_data").fetchall()
        conn.close()

        tasks = [self.extract_and_store_async(jid, txt) for jid, txt in rows]
        return await asyncio.gather(*tasks)

if __name__ == "__main__":
    processor = AcademicDetailsProcessor()
    # synchronous
    all_sync = processor.batch_extract()
    # asynchronous
    all_async = asyncio.run(processor.batch_extract_async())
    for res in all_sync:
        print(res.model_dump_json(indent=2))
    # optionally inspect async results
    # for res in all_async:
    #     print(res.model_dump_json(indent=2))
