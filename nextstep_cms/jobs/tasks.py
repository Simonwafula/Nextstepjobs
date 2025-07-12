from celery import shared_task
from django.utils import timezone
from django.db import transaction
import logging
import asyncio
from typing import List, Dict, Any

from .models import JobPosting, ProcessedJob, Company
from ai_engine.models import AIConfiguration
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def scrape_jobs_from_sources(self, sources: List[str], search_terms: List[str], location: str = None, limit_per_source: int = 50):
    """
    Scrape jobs from multiple sources
    """
    try:
        from scrapers.linkedin_scraper import LinkedInScraper
        from scrapers.indeed_scraper import IndeedScraper
        from scrapers.brighter_monday_scraper import BrighterMondayScraper
        
        scrapers = {
            'linkedin': LinkedInScraper(),
            'indeed': IndeedScraper(),
            'brighter_monday': BrighterMondayScraper(),
        }
        
        all_jobs = []
        
        for source_name in sources:
            if source_name not in scrapers:
                logger.warning(f"Unknown scraper source: {source_name}")
                continue
                
            try:
                scraper = scrapers[source_name]
                jobs = scraper.scrape_job_listings(
                    search_terms=search_terms,
                    location=location,
                    limit=limit_per_source
                )
                
                # Store jobs in database
                stored_jobs = []
                for job_data in jobs:
                    try:
                        # Get or create company
                        company, created = Company.objects.get_or_create(
                            name=job_data.get('company_name', 'Unknown'),
                            defaults={
                                'slug': job_data.get('company_name', 'unknown').lower().replace(' ', '-'),
                                'description': job_data.get('company_description', ''),
                                'website': job_data.get('company_website'),
                            }
                        )
                        
                        # Create job posting
                        job_posting = JobPosting.objects.create(
                            source=source_name,
                            external_id=job_data.get('external_id'),
                            source_url=job_data.get('url', ''),
                            title=job_data.get('title', ''),
                            company=company,
                            description=job_data.get('description', ''),
                            requirements=job_data.get('requirements', ''),
                            location=job_data.get('location'),
                            remote_friendly=job_data.get('remote_friendly', False),
                            job_type=job_data.get('job_type', 'full_time'),
                            experience_level=job_data.get('experience_level'),
                            salary_min=job_data.get('salary_min'),
                            salary_max=job_data.get('salary_max'),
                            posted_date=job_data.get('posted_date'),
                            scraped_at=timezone.now(),
                        )
                        
                        stored_jobs.append(job_posting)
                        
                    except Exception as job_error:
                        logger.error(f"Error storing job from {source_name}: {job_error}")
                        continue
                
                all_jobs.extend(stored_jobs)
                logger.info(f"Scraped and stored {len(stored_jobs)} jobs from {source_name}")
                
            except Exception as scraper_error:
                logger.error(f"Error scraping from {source_name}: {scraper_error}")
                continue
        
        # Queue jobs for processing
        job_ids = [job.id for job in all_jobs]
        if job_ids:
            process_job_batch.delay(job_ids)
        
        return {
            'total_jobs_scraped': len(all_jobs),
            'job_ids': job_ids,
            'sources_used': sources
        }
        
    except Exception as exc:
        logger.error(f"Error in scrape_jobs_from_sources: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def process_job_batch(self, job_ids: List[str], batch_size: int = 5):
    """
    Process a batch of jobs with AI analysis
    """
    try:
        jobs = JobPosting.objects.filter(id__in=job_ids, is_processed=False)
        
        processed_count = 0
        
        for job in jobs:
            try:
                # Process individual job
                result = process_single_job(job.id)
                if result['success']:
                    processed_count += 1
                    
            except Exception as job_error:
                logger.error(f"Error processing job {job.id}: {job_error}")
                continue
        
        logger.info(f"Processed {processed_count} out of {len(job_ids)} jobs")
        
        return {
            'processed_count': processed_count,
            'total_jobs': len(job_ids),
            'success_rate': processed_count / len(job_ids) if job_ids else 0
        }
        
    except Exception as exc:
        logger.error(f"Error in process_job_batch: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def process_single_job(self, job_id: str):
    """
    Process a single job with AI analysis
    """
    try:
        job = JobPosting.objects.get(id=job_id)
        
        if job.is_processed:
            return {'success': True, 'message': 'Job already processed'}
        
        # Mark as processing
        job.processing_status = 'processing'
        job.save()
        
        # Get AI configuration for job analysis
        try:
            ai_config = AIConfiguration.objects.get(
                config_type='job_analysis',
                is_active=True
            )
        except AIConfiguration.DoesNotExist:
            ai_config = None
        
        # Prepare job data for AI analysis
        job_text = f"""
        Job Title: {job.title}
        Company: {job.company.name}
        Location: {job.location}
        Job Type: {job.job_type}
        
        Description:
        {job.description}
        
        Requirements:
        {job.requirements or 'Not specified'}
        """
        
        # Get AI analysis
        ai_analysis = get_job_ai_analysis(job_text, ai_config)
        
        if ai_analysis:
            # Create processed job record
            with transaction.atomic():
                processed_job = ProcessedJob.objects.create(
                    original_job=job,
                    ai_summary=ai_analysis.get('summary', ''),
                    ai_industry_category=ai_analysis.get('industry', ''),
                    ai_role_level=ai_analysis.get('role_level', ''),
                    ai_company_culture=ai_analysis.get('company_culture', ''),
                    required_skills=ai_analysis.get('required_skills', []),
                    preferred_skills=ai_analysis.get('preferred_skills', []),
                    technical_skills=ai_analysis.get('technical_skills', []),
                    soft_skills=ai_analysis.get('soft_skills', []),
                    education_requirements=ai_analysis.get('education_requirements', {}),
                    experience_requirements=ai_analysis.get('experience_requirements', {}),
                    certifications_required=ai_analysis.get('certifications', []),
                    complexity_score=ai_analysis.get('complexity_score', 0.5),
                    competitiveness_score=ai_analysis.get('competitiveness_score', 0.5),
                    growth_potential=ai_analysis.get('growth_potential', ''),
                    keywords=ai_analysis.get('keywords', []),
                    tags=ai_analysis.get('tags', []),
                    completeness_score=ai_analysis.get('completeness_score', 0.5),
                    accuracy_score=ai_analysis.get('accuracy_score', 0.5),
                )
                
                # Update original job
                job.is_processed = True
                job.processing_status = 'completed'
                job.processed_at = timezone.now()
                job.quality_score = ai_analysis.get('quality_score', 0.5)
                job.save()
            
            # Queue job matching for all users
            queue_job_matching_for_all_users.delay(str(processed_job.id))
            
            return {'success': True, 'processed_job_id': str(processed_job.id)}
        
        else:
            # Mark as failed
            job.processing_status = 'failed'
            job.save()
            return {'success': False, 'message': 'AI analysis failed'}
        
    except JobPosting.DoesNotExist:
        return {'success': False, 'message': 'Job not found'}
    except Exception as exc:
        logger.error(f"Error processing job {job_id}: {exc}")
        # Mark job as failed
        try:
            job = JobPosting.objects.get(id=job_id)
            job.processing_status = 'failed'
            job.save()
        except:
            pass
        raise self.retry(exc=exc, countdown=60)


def get_job_ai_analysis(job_text: str, ai_config: AIConfiguration = None) -> Dict[str, Any]:
    """
    Get AI analysis for a job posting
    """
    try:
        import os
        
        # Use AI configuration or default
        if ai_config:
            system_prompt = ai_config.system_prompt
            temperature = ai_config.temperature
            max_tokens = ai_config.max_tokens
            model = ai_config.model_name
        else:
            system_prompt = """You are an expert job market analyst. Analyze job postings and extract structured information about requirements, skills, and characteristics. Respond in JSON format with the following structure:
            {
                "summary": "Brief job summary",
                "industry": "Industry category",
                "role_level": "Experience level (Entry/Junior/Mid/Senior/Lead)",
                "company_culture": "Company culture indicators",
                "required_skills": ["skill1", "skill2"],
                "preferred_skills": ["skill1", "skill2"],
                "technical_skills": ["tech1", "tech2"],
                "soft_skills": ["soft1", "soft2"],
                "education_requirements": {"level": "degree level", "field": "field of study"},
                "experience_requirements": {"years": 3, "type": "specific experience"},
                "certifications": ["cert1", "cert2"],
                "complexity_score": 0.7,
                "competitiveness_score": 0.6,
                "growth_potential": "High/Medium/Low",
                "keywords": ["keyword1", "keyword2"],
                "tags": ["tag1", "tag2"],
                "completeness_score": 0.8,
                "accuracy_score": 0.9,
                "quality_score": 0.85
            }"""
            temperature = 0.3
            max_tokens = 2000
            model = "gpt-4"
        
        # Initialize AI chat
        chat = LlmChat(
            api_key=os.environ.get('OPENAI_API_KEY'),
            session_id=f"job_analysis_{timezone.now().timestamp()}",
            system_message=system_prompt
        ).with_model("openai", model)
        
        # Send message
        message = UserMessage(text=job_text)
        response = asyncio.run(chat.send_message(message))
        
        # Parse JSON response
        import json
        try:
            analysis = json.loads(response)
            return analysis
        except json.JSONDecodeError:
            # If not valid JSON, create basic structure
            return {
                "summary": response[:200] + "..." if len(response) > 200 else response,
                "industry": "Unknown",
                "role_level": "Unknown",
                "required_skills": [],
                "quality_score": 0.3
            }
        
    except Exception as e:
        logger.error(f"Error in AI job analysis: {e}")
        return None


@shared_task(bind=True)
def queue_job_matching_for_all_users(self, processed_job_id: str):
    """
    Queue job matching calculation for all users
    """
    try:
        from profiles.models import UserProfile
        from .models import ProcessedJob
        
        processed_job = ProcessedJob.objects.get(id=processed_job_id)
        active_users = UserProfile.objects.filter(profile_completed=True)
        
        for user in active_users:
            calculate_job_match.delay(str(user.id), processed_job_id)
        
        logger.info(f"Queued job matching for {active_users.count()} users for job {processed_job_id}")
        
    except Exception as e:
        logger.error(f"Error queuing job matching: {e}")


@shared_task(bind=True, max_retries=2)
def calculate_job_match(self, user_id: str, processed_job_id: str):
    """
    Calculate job match score for a user and job
    """
    try:
        from profiles.models import UserProfile
        from .models import ProcessedJob, JobMatch
        
        user = UserProfile.objects.get(id=user_id)
        processed_job = ProcessedJob.objects.get(id=processed_job_id)
        
        # Check if match already exists
        if JobMatch.objects.filter(user_profile=user, job=processed_job).exists():
            return {'message': 'Match already exists'}
        
        # Calculate match scores
        match_scores = calculate_match_scores(user, processed_job)
        
        # Create job match record
        job_match = JobMatch.objects.create(
            user_profile=user,
            job=processed_job,
            overall_match_score=match_scores['overall'],
            skills_match_score=match_scores['skills'],
            experience_match_score=match_scores['experience'],
            location_match_score=match_scores['location'],
            education_match_score=match_scores['education'],
            matching_skills=match_scores['matching_skills'],
            missing_skills=match_scores['missing_skills'],
            recommendations=match_scores['recommendations'],
        )
        
        return {'success': True, 'match_id': str(job_match.id), 'score': match_scores['overall']}
        
    except Exception as exc:
        logger.error(f"Error calculating job match for user {user_id}, job {processed_job_id}: {exc}")
        raise self.retry(exc=exc, countdown=30)


def calculate_match_scores(user: 'UserProfile', processed_job: 'ProcessedJob') -> Dict[str, Any]:
    """
    Calculate detailed match scores between user and job
    """
    # Get user skills
    user_skills = set(skill.skill.name.lower() for skill in user.skills.all())
    user_experience = user.experience_years
    user_education = user.education_level
    user_locations = set(loc.lower() for loc in user.preferred_locations)
    
    # Get job requirements
    job_skills = set(skill.lower() for skill in processed_job.required_skills + processed_job.preferred_skills)
    job_location = processed_job.original_job.location
    
    # Skills matching
    matching_skills = list(user_skills.intersection(job_skills))
    missing_skills = list(job_skills - user_skills)
    skills_score = len(matching_skills) / len(job_skills) if job_skills else 1.0
    
    # Experience matching
    exp_req = processed_job.experience_requirements.get('years', 0) if processed_job.experience_requirements else 0
    if user_experience >= exp_req:
        experience_score = 1.0
    elif user_experience >= exp_req * 0.7:
        experience_score = 0.8
    else:
        experience_score = 0.4
    
    # Location matching
    if not job_location or processed_job.original_job.remote_friendly:
        location_score = 1.0
    elif any(loc in job_location.lower() for loc in user_locations):
        location_score = 1.0
    else:
        location_score = 0.3
    
    # Education matching
    education_score = 0.8  # Default score
    
    # Overall score (weighted average)
    overall_score = (
        skills_score * 0.4 +
        experience_score * 0.3 +
        location_score * 0.2 +
        education_score * 0.1
    )
    
    # Recommendations
    recommendations = []
    if len(missing_skills) > 0:
        recommendations.append(f"Consider developing these skills: {', '.join(missing_skills[:3])}")
    if user_experience < exp_req:
        recommendations.append(f"This role typically requires {exp_req} years of experience")
    
    return {
        'overall': round(overall_score, 3),
        'skills': round(skills_score, 3),
        'experience': round(experience_score, 3),
        'location': round(location_score, 3),
        'education': round(education_score, 3),
        'matching_skills': matching_skills,
        'missing_skills': missing_skills,
        'recommendations': recommendations,
    }


@shared_task(bind=True)
def cleanup_old_jobs(self, days_old: int = 30):
    """
    Clean up old job postings and related data
    """
    try:
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        # Mark old jobs as expired
        expired_count = JobPosting.objects.filter(
            posted_date__lt=cutoff_date,
            is_expired=False
        ).update(is_expired=True, is_active=False)
        
        logger.info(f"Marked {expired_count} jobs as expired")
        
        return {'expired_jobs': expired_count}
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_jobs: {e}")
        return {'error': str(e)}