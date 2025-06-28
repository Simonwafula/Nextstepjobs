from langchain.chains.llm import LLMChain
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal, Dict, Any

import sqlite3
import pandas as pd
import json
import re
import os
import logging

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
        description="The specific field of study (e.g., 'supply chain management', 'computer science')"
    )

    requirement_type: Literal["required", "preferred", "equivalent_experience_accepted"] = Field(
        description="Whether this education is required, preferred, or if equivalent experience is accepted"
    )

    years_experience_substitute: Optional[int] = Field(
        description="Number of years of experience that can substitute for this education"
    )

    confidence_score: float = Field(
        description="Confidence score for this extraction (0.0 to 1.0)"
    )


class EducationExtraction(BaseModel):
    """Container for all education requirements extracted from a job posting"""
    requirements: List[EducationRequirement] = Field(
        description="List of all education requirements found"
    )

    raw_text_analyzed: str = Field(
        description="The original text that was analyzed"
    )


class AcademicDetailsProcessor:
    """
    Specialized processor for extracting academic requirements from job postings
    """

    def __init__(self,
                 input_db_path: str = "jobs.sqlite3",
                 output_db_path: str = "processed_jobs.sqlite3",
                 llm_model="gpt-4o-mini",
                 temperature=0.1):
        self.llm = OpenAI(model_name=llm_model, temperature=temperature)
        self.output_parser = PydanticOutputParser(pydantic_object=EducationExtraction)
        self.chain = self._create_extraction_chain()

        # Initialize databases
        self._setup_output_database()

        # Pre-defined mappings for normalization
        self.level_mappings = {
            # High School variants
            "high school": "high_school",
            "hs diploma": "high_school",
            "secondary school": "high_school",
            "matric": "high_school",

            # Certificate variants
            "certificate": "certificate",
            "cert": "certificate",
            "certification": "certificate",
            "professional certificate": "certificate",

            # Diploma variants
            "diploma": "diploma",
            "advanced diploma": "diploma",
            "national diploma": "diploma",
            "higher diploma": "diploma",

            # Associate variants
            "associate": "associate",
            "associate degree": "associate",
            "aa": "associate",
            "as": "associate",
            "aas": "associate",

            # Bachelor variants
            "bachelor": "bachelor",
            "bachelors": "bachelor",
            "bachelor's": "bachelor",
            "ba": "bachelor",
            "bs": "bachelor",
            "b.a": "bachelor",
            "b.s": "bachelor",
            "bsc": "bachelor",
            "undergraduate": "bachelor",

            # Master variants
            "master": "master",
            "masters": "master",
            "master's": "master",
            "ma": "master",
            "ms": "master",
            "m.a": "master",
            "m.s": "master",
            "msc": "master",
            "mba": "master",
            "graduate": "master",

            # PhD variants
            "phd": "phd",
            "ph.d": "phd",
            "doctorate": "phd",
            "doctoral": "phd",
            "doctor": "phd",

            # Professional License
            "license": "professional_license",
            "licence": "professional_license",
            "professional license": "professional_license",
            "certification": "professional_license",
        }

        # Common field mappings and synonyms
        # Field normalization mappings
        self.field_mappings = {
            "computer science": ["cs", "computer sci", "computing", "informatics", "software engineering"],
            "information technology": ["it", "info tech", "information systems", "mis"],
            "business administration": ["business admin", "business", "management", "business management"],
            "supply chain management": ["supply chain", "logistics", "operations management", "procurement"],
            "mechanical engineering": ["mech eng", "mechanical", "mechanical tech"],
            "electrical engineering": ["ee", "electrical", "electronic engineering", "electronics"],
            "data science": ["data analytics", "analytics", "data analysis", "statistics"],
            "marketing": ["digital marketing", "marketing communications", "advertising"],
            "finance": ["financial management", "accounting and finance", "economics"],
            "human resources": ["hr", "human resource management", "people management"],
            "healthcare": ["nursing", "medical", "health sciences", "public health"],
            "education": ["teaching", "educational leadership", "curriculum"],
            "accounting": ["cpa", "bookkeeping", "financial accounting"],
            "project management": ["pmp", "program management", "operations"],
            "psychology": ["counseling", "behavioral science", "social work"],
        }

    def _create_extraction_chain(self):
        """Create the LangChain extraction chain"""

        prompt_template = """
        You are an expert at extracting education requirements from job postings. 
        Your task is to identify ALL education requirements mentioned in the job text and extract them with high precision.

        CRITICAL PARSING RULES:
        1. EDUCATION LEVELS - Distinguish precisely between:
           - high_school: High school diploma, secondary education
           - certificate: Short-term certificates (weeks to months)
           - diploma: Diploma programs (typically 1-2 years, vocational/technical)
           - associate: Associate degrees (2-year college degrees)
           - bachelor: Bachelor's degrees (4-year university degrees)
           - master: Master's degrees (graduate level)
           - phd: Doctoral degrees
           - professional_license: CPA, PE, RN, etc.
           - equivalent_experience: When only experience is mentioned as substitute

        2. FIELD EXTRACTION - Extract the EXACT field mentioned:
           - "Bachelor's in Supply Chain Management" → field: "supply chain management"
           - "Diploma in Mechanical Engineering" → field: "mechanical engineering"  
           - "Degree in related field" → field: "related field"
           - "Business degree" → field: "business"

        3. REQUIREMENT TYPES:
           - required: Must have this education
           - preferred: Nice to have but not mandatory
           - equivalent_experience_accepted: Experience can substitute

        4. EXPERIENCE SUBSTITUTION:
           - Extract years if mentioned: "or 5 years equivalent experience" → 5

        EXAMPLES:
        - "Bachelor's degree in Supply Chain Management required" 
          → level: "bachelor", field: "supply chain management", requirement_type: "required"

        - "Diploma in Computer Science or equivalent experience"
          → level: "diploma", field: "computer science", requirement_type: "equivalent_experience_accepted"

        - "MBA preferred, or Bachelor's with 5+ years experience"
          → Two requirements: MBA (preferred) and Bachelor's with experience substitute

        TEXT TO ANALYZE:
        {job_content}

        {format_instructions}

        Extract ALL education requirements found in the text. If no specific education is mentioned, return an empty requirements list.
        Assign confidence scores based on how explicitly the requirement is stated (0.9+ for explicit, 0.7+ for implied, 0.5+ for inferred).
        """

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["job_text"],
            partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
        )

        return LLMChain(llm=self.llm, prompt=prompt, output_parser=self.output_parser)

    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess the job text for better extraction"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Normalize common abbreviations
        text = re.sub(r'\bB\.S\.\b', 'Bachelor', text, flags=re.IGNORECASE)
        text = re.sub(r'\bB\.A\.\b', 'Bachelor', text, flags=re.IGNORECASE)
        text = re.sub(r'\bM\.S\.\b', 'Master', text, flags=re.IGNORECASE)
        text = re.sub(r'\bM\.A\.\b', 'Master', text, flags=re.IGNORECASE)
        text = re.sub(r'\bPh\.D\.\b', 'PhD', text, flags=re.IGNORECASE)

        return text.strip()

    def _post_process_results(self, extraction: EducationExtraction) -> EducationExtraction:
        """Post-process and validate extraction results"""
        processed_requirements = []

        for req in extraction.requirements:
            # Normalize field names
            if req.field:
                req.field = self._normalize_field_name(req.field)

            # Validate confidence scores
            if req.confidence_score > 1.0:
                req.confidence_score = 1.0
            elif req.confidence_score < 0.0:
                req.confidence_score = 0.0

            processed_requirements.append(req)

        extraction.requirements = processed_requirements
        return extraction

    def _normalize_field_name(self, field: str) -> str:
        """Normalize field names to standard format"""
        field_lower = field.lower().strip()

        # Check for exact matches in our mappings
        for standard_name, variants in self.field_mappings.items():
            if field_lower == standard_name or field_lower in variants:
                return standard_name

        # Return original if no mapping found
        return field.lower().strip()

    def extract_academic_details(self, job_text: str) -> EducationExtraction:
        """
        Main method to extract academic details from job text

        Args:
            job_text (str): The job posting text to analyze

        Returns:
            EducationExtraction: Structured extraction results
        """
        try:
            # Preprocess the text
            processed_text = self._preprocess_text(job_text)

            # Run the extraction chain
            result = self.chain.run(job_text=processed_text)

            # Post-process results
            result = self._post_process_results(result)

            logger.info(f"Successfully extracted {len(result.requirements)} education requirements")
            return result

        except OutputParserException as e:
            logger.error(f"Output parsing error: {e}")
            # Return empty result with error info
            return EducationExtraction(
                requirements=[],
                raw_text_analyzed=job_text[:200] + "..." if len(job_text) > 200 else job_text
            )
        except Exception as e:
            logger.error(f"Unexpected error during extraction: {e}")
            raise

    def batch_extract(self, job_texts: List[str]) -> List[EducationExtraction]:
        """
        Extract academic details from multiple job postings

        Args:
            job_texts (List[str]): List of job posting texts

        Returns:
            List[EducationExtraction]: List of extraction results
        """
        results = []
        for i, text in enumerate(job_texts):
            try:
                result = self.extract_academic_details(text)
                results.append(result)
                logger.info(f"Processed job posting {i + 1}/{len(job_texts)}")
            except Exception as e:
                logger.error(f"Error processing job posting {i + 1}: {e}")
                # Add empty result for failed extractions
                results.append(EducationExtraction(
                    requirements=[],
                    raw_text_analyzed=text[:200] + "..." if len(text) > 200 else text
                ))

        return results


# Usage Example and Testing
if __name__ == "__main__":
    # Initialize the processor
    processor = AcademicDetailsProcessor()

    # Test cases
    test_job_postings = [
        """
        We are seeking a Supply Chain Manager with a Bachelor's degree in Supply Chain Management, 
        Logistics, or related field. MBA preferred. Candidates with a Diploma in Operations Management 
        and 8+ years of experience will also be considered.
        """,

        """
        Software Engineer position requires a Bachelor's degree in Computer Science or equivalent. 
        Master's degree preferred. Professional certifications in cloud computing are a plus.
        Candidates with 5+ years of relevant experience may be considered in lieu of degree requirements.
        """,

        """
        Entry-level Marketing Assistant position. High school diploma required. 
        Certificate in Digital Marketing preferred but not mandatory.
        """,

        """
        Senior Mechanical Engineer - PhD in Mechanical Engineering required. 
        Professional Engineer (PE) license mandatory. 10+ years of industry experience.
        """
    ]

    # Process each test case
    for i, job_text in enumerate(test_job_postings, 1):
        print(f"\n=== TEST CASE {i} ===")
        print(f"Job Text: {job_text.strip()}")

        try:
            result = processor.extract_academic_details(job_text)
            print(f"\nExtracted {len(result.requirements)} education requirements:")

            for j, req in enumerate(result.requirements, 1):
                print(f"{j}. Level: {req.level}")
                print(f"   Field: {req.field}")
                print(f"   Type: {req.requirement_type}")
                print(f"   Experience Substitute: {req.years_experience_substitute}")
                print(f"   Confidence: {req.confidence_score:.2f}")
                print()

        except Exception as e:
            print(f"Error: {e}")

    # Example of batch processing
    print("\n=== BATCH PROCESSING EXAMPLE ===")
    batch_results = processor.batch_extract(test_job_postings)
    print(f"Processed {len(batch_results)} job postings in batch")

    # Summary statistics
    total_requirements = sum(len(result.requirements) for result in batch_results)
    print(f"Total education requirements extracted: {total_requirements}")