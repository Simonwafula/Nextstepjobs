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
    
    def __init__(self):
        self.session = None
        self.ai_client = None
        self._init_ai_client()
        
    def _init_ai_client(self):
        """Initialize AI client for content processing"""
        try:
            self.ai_client = LlmChat(api_key=os.environ.get('OPENAI_API_KEY'))
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {e}")
            
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
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    async def process_job(self, job_record: Dict) -> Dict:
        """
        Process a single job record and extract structured information
        
        Args:
            job_record: Basic job data with title and link
            
        Returns:
            Processed job data with extracted information
        """
        try:
            logger.info(f"Processing job: {job_record.get('title', 'Unknown')}")
            
            # Fetch full job content
            job_content = await self._fetch_job_content(job_record['link'])
            if not job_content:
                logger.warning(f"Failed to fetch content for {job_record['link']}")
                return self._create_failed_record(job_record, "Failed to fetch content")
            
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
        try:
            async with self.session.get(job_url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"HTTP {response.status} for {job_url}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching {job_url}: {e}")
            return None
            
    async def _extract_job_information(self, html_content: str, job_record: Dict) -> Dict:
        """
        Extract structured information from job posting HTML
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Get clean text
        text_content = soup.get_text(separator=' ', strip=True)
        
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
        
        return extracted
        
    def _extract_company(self, soup: BeautifulSoup, text: str) -> str:
        """Extract company name"""
        # Try structured selectors first
        company_selectors = [
            '.company-name', '.company', '[data-testid="company-name"]',
            '.employer-name', '.job-company', 'span.companyName'
        ]
        
        for selector in company_selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
                
        # Fallback to text pattern matching
        company_patterns = [
            r'Company:\s*([^\n]+)',
            r'Employer:\s*([^\n]+)',
            r'Organization:\s*([^\n]+)'
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
                
        return "Unknown"
        
    def _extract_location(self, soup: BeautifulSoup, text: str) -> str:
        """Extract job location"""
        # Try structured selectors
        location_selectors = [
            '.location', '.job-location', '[data-testid="job-location"]',
            '.workplace-location', '.job-address'
        ]
        
        for selector in location_selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
                
        # Pattern matching for Kenyan locations
        kenyan_cities = ['Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Thika', 'Machakos']
        for city in kenyan_cities:
            if city.lower() in text.lower():
                return city
                
        return "Kenya"
        
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
        
        text_lower = text.lower()
        for job_type, keywords in job_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return job_type.title()
                
        return "Full-time"  # Default
        
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
        
        text_lower = text.lower()
        
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
                
        # Check for level keywords
        for pattern, level in experience_patterns[1:]:
            if re.search(pattern, text_lower):
                return level
                
        return "Mid Level"  # Default
        
    def _extract_salary(self, soup: BeautifulSoup, text: str) -> Optional[Dict]:
        """Extract salary information"""
        # Try structured selectors
        salary_selectors = [
            '.salary', '.compensation', '.pay', '.salaryText'
        ]
        
        for selector in salary_selectors:
            elem = soup.select_one(selector)
            if elem:
                salary_text = elem.get_text(strip=True)
                return self._parse_salary(salary_text)
                
        # Pattern matching for salary
        salary_patterns = [
            r'salary:?\s*([^\n]+)',
            r'compensation:?\s*([^\n]+)',
            r'ksh\s*[\d,]+',
            r'kes\s*[\d,]+',
            r'\$\s*[\d,]+',
            r'[\d,]+\s*-\s*[\d,]+\s*(?:per|/)\s*(?:month|year)'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_salary(match.group(0))
                
        return None
        
    def _parse_salary(self, salary_text: str) -> Dict:
        """Parse salary text into structured format"""
        # Extract numbers
        numbers = re.findall(r'[\d,]+', salary_text.replace(',', ''))
        currency = 'KSH'
        
        if '$' in salary_text:
            currency = 'USD'
        elif 'kes' in salary_text.lower():
            currency = 'KES'
            
        period = 'month'
        if any(word in salary_text.lower() for word in ['year', 'annual', 'yearly']):
            period = 'year'
            
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
            
        return {'raw': salary_text}
        
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract job description"""
        description_selectors = [
            '.job-description', '.description', '.job-details',
            '.job-summary', '.overview', '.about-role'
        ]
        
        for selector in description_selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(separator=' ', strip=True)[:2000]
                
        # Fallback to main content
        main_content = soup.find('main') or soup.find('body')
        if main_content:
            return main_content.get_text(separator=' ', strip=True)[:2000]
            
        return ""
        
    def _extract_requirements(self, text: str) -> List[str]:
        """Extract job requirements"""
        requirements = []
        
        # Look for requirements sections
        req_sections = re.findall(
            r'(?:requirements?|qualifications?|must have|essential)[:\n](.*?)(?=\n[A-Z]|\n\n|$)',
            text, re.IGNORECASE | re.DOTALL
        )
        
        for section in req_sections:
            # Split by bullet points or line breaks
            items = re.split(r'[•\n]\s*', section.strip())
            for item in items:
                clean_item = item.strip()
                if len(clean_item) > 10 and len(clean_item) < 200:
                    requirements.append(clean_item)
                    
        return requirements[:10]  # Limit to 10 requirements
        
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
        
        skills = set()
        text_lower = text.lower()
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            skills.update(matches)
            
        # Add soft skills
        soft_skills = ['communication', 'leadership', 'teamwork', 'problem solving', 'analytical']
        for skill in soft_skills:
            if skill in text_lower:
                skills.add(skill.title())
                
        return list(skills)[:15]  # Limit to 15 skills
        
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
        
        found_benefits = []
        text_lower = text.lower()
        
        for benefit in benefits_keywords:
            if benefit in text_lower:
                found_benefits.append(benefit.title())
                
        return found_benefits[:10]
        
    def _extract_deadline(self, soup: BeautifulSoup, text: str) -> Optional[str]:
        """Extract application deadline"""
        deadline_selectors = [
            '.deadline', '.closing-date', '.application-deadline'
        ]
        
        for selector in deadline_selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
                
        # Pattern matching
        deadline_patterns = [
            r'deadline:?\s*([^\n]+)',
            r'closing date:?\s*([^\n]+)',
            r'apply by:?\s*([^\n]+)'
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
                
        return None
        
    def _extract_education(self, text: str) -> List[str]:
        """Extract education requirements"""
        education_levels = [
            'Bachelor', 'Master', 'PhD', 'Doctorate', 'Degree',
            'Diploma', 'Certificate', 'Associate'
        ]
        
        found_education = []
        text_lower = text.lower()
        
        for level in education_levels:
            if level.lower() in text_lower:
                found_education.append(level)
                
        return found_education
        
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
            
            response = await self.ai_client.chat([UserMessage(content=prompt)])
            
            # Parse AI response
            try:
                ai_data = json.loads(response.content)
                return ai_data
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI response as JSON")
                return {}
                
        except Exception as e:
            logger.error(f"Error in AI enhancement: {e}")
            return {}
            
    def _create_processed_record(self, original_record: Dict, extracted_data: Dict, ai_data: Dict) -> Dict:
        """Create final processed job record"""
        processed_record = {
            # Original data
            'id': original_record['id'],
            'source': original_record['source'],
            'scraped_at': original_record['scraped_at'],
            'link': original_record['link'],
            
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
            
            # AI-enhanced data
            'ai_skills_analysis': ai_data.get('skills_analysis', []),
            'ai_experience_summary': ai_data.get('experience_summary', ''),
            'ai_role_level': ai_data.get('role_level', ''),
            'remote_friendly': ai_data.get('remote_friendly', False),
            'growth_potential': ai_data.get('growth_potential', 'Medium'),
            'ai_industry_category': ai_data.get('industry_category', ''),
            'key_responsibilities': ai_data.get('key_responsibilities', []),
            
            # Metadata
            'processed': True,
            'processed_at': datetime.utcnow(),
            'quality_score': self._calculate_quality_score(extracted_data, ai_data)
        }
        
        return processed_record
        
    def _calculate_quality_score(self, extracted_data: Dict, ai_data: Dict) -> float:
        """Calculate quality score for processed job (0-1)"""
        score = 0.0
        
        # Check completeness of key fields
        if extracted_data.get('title'): score += 0.2
        if extracted_data.get('company') and extracted_data['company'] != 'Unknown': score += 0.1
        if extracted_data.get('description'): score += 0.2
        if extracted_data.get('skills'): score += 0.1
        if extracted_data.get('requirements'): score += 0.1
        if extracted_data.get('salary'): score += 0.1
        if ai_data.get('skills_analysis'): score += 0.1
        if ai_data.get('key_responsibilities'): score += 0.1
        
        return min(1.0, score)
        
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


# Convenience function for processing batches
async def process_job_batch(job_records: List[Dict], batch_size: int = 5) -> List[Dict]:
    """
    Process a batch of job records
    """
    processed_jobs = []
    
    async with JobProcessor() as processor:
        # Process jobs in smaller batches to avoid overwhelming servers
        for i in range(0, len(job_records), batch_size):
            batch = job_records[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [processor.process_job(job) for job in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch processing error: {result}")
                else:
                    processed_jobs.append(result)
                    
            # Small delay between batches
            if i + batch_size < len(job_records):
                await asyncio.sleep(2)
                
    return processed_jobs