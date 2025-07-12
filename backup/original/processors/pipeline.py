# processors/pipeline.py
import warnings

from urllib3.exceptions import NotOpenSSLWarning

# Suppress only the LibreSSL/OpenSSL compatibility warning before any urllib3 imports
warnings.filterwarnings(
    "ignore",
    category=NotOpenSSLWarning,
    module="urllib3"
)

import os
import json
import sqlite3
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Tuple

from dotenv import load_dotenv
from langchain_core.exceptions import OutputParserException

# Load environment variables from .env file
load_dotenv()

from langchain.chains.llm import LLMChain
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI
from processors.models import JobStructured

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")

# Environment & DB settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Please set OPENAI_API_KEY environment variable.")

RAW_DB       = os.getenv("JOB_DB_PATH", "db/jobs.sqlite3")
RAW_TABLE    = os.getenv("RAW_TABLE", "jobs_data")
STRUCT_DB    = os.getenv("STRUCT_DB_PATH", "db/jobs_structured.sqlite3")
STRUCT_TABLE = os.getenv("STRUCT_TABLE", "jobs_structured")

# Initialize structured DB
def ensure_structured_db():
    conn = sqlite3.connect(STRUCT_DB)
    conn.execute(
        f"CREATE TABLE IF NOT EXISTS {STRUCT_TABLE} (id INTEGER PRIMARY KEY, json TEXT)"
    )
    conn.commit()
    conn.close()
    logging.info("Structured database initialized.")

# Fetch raw records
def fetch_raw(batch_size: int) -> List[Tuple[int, str]]:
    conn = sqlite3.connect(RAW_DB)
    cur  = conn.cursor()
    cur.execute(f"SELECT id, content FROM {RAW_TABLE} LIMIT ?", (batch_size,))
    rows = cur.fetchall()
    conn.close()
    return rows

# Persist structured results
def persist_structured(records: List[Tuple[int, str]]):
    conn = sqlite3.connect(STRUCT_DB)
    cur  = conn.cursor()
    cur.executemany(
        f"INSERT OR REPLACE INTO {STRUCT_TABLE} (id, json) VALUES (?,?)",
        records
    )
    conn.commit()
    conn.close()
    logging.info(f"Saved {len(records)} structured records.")

# Setup LangChain with format instructions
def create_chain():
    # Initialize Pydantic parser for schema enforcement
    parser = PydanticOutputParser(pydantic_object=JobStructured)

    # Base prompt template with placeholder for format instructions
    prompt_template = PromptTemplate(
        input_variables=["description", "format_instructions"],
        template="""
You are an expert at extracting structured JSON from job description text.
Return exactly the JSON matching the JobStructured schema.

Job Description:
{description}

{
  "id": int,
  "company_name": string,
  "location": string,
  "post_date": string (YYYY-MM-DD or empty),
  "education_requirements": [
    {
      "level": "diploma|certificate|associate|bachelor|master|phd|professional_license|none_specified",
      "field": string,
      "requirement_type": "required|preferred|equivalent_experience_accepted",
      "years_experience_in_lieu": number or null
    }
  ],
  "job_classification": { /* follow JobClassification model */ },
  "location_and_work": { /* follow LocationWork model */ },
  "skills": { /* follow SkillsTaxonomy model */ },
  "certifications": [ /* list of Certification objects */ ],
  "career_progression": { /* follow CareerProgression model */ },
  "compensation": { /* follow CompensationBenefits model */ },
  "market_intelligence": { /* follow MarketIntelligence model */ },
  "work_environment": { /* follow WorkEnvironment model */ }
}

{format_instructions}
"""
    )

    # Inject format instructions so chain only needs 'description'
    prompt = prompt_template.partial(
        format_instructions=parser.get_format_instructions()
    )

    llm = OpenAI(temperature=0)
    chain = LLMChain(
        llm=llm,
        prompt=prompt
    )
    return chain, parser

# Process a single record with validation with validation
def process_record(record: Tuple[int, str], chain: LLMChain, parser: PydanticOutputParser) -> Optional[Tuple[int, str]]:
    job_id, text = record
    try:
        response = chain.invoke({"description": text})
        # Parse and validate
        structured: JobStructured = parser.parse(response)
        data = structured.dict()
        return (job_id, json.dumps(data))
    except OutputParserException as e:
        logging.error(f"Parsing failed id={job_id}: {e}")
    except Exception as e:
        logging.error(f"Failed to process id={job_id}: {e}")
    return None

# Main batch processing
def main(batch: int = 10, workers: int = 5):
    ensure_structured_db()
    raw_records = fetch_raw(batch)
    if not raw_records:
        logging.info("No new records to process.")
        return

    chain, parser = create_chain()
    results = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(process_record, r, chain, parser) for r in raw_records]
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                results.append(res)

    persist_structured(results)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Process raw job descriptions to structured JSON.")
    parser.add_argument("--batch", type=int, default=10)
    parser.add_argument("--workers", type=int, default=5)
    args = parser.parse_args()
    main(batch=args.batch, workers=args.workers)
