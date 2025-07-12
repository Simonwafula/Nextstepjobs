from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from wagtail.models import Site, Page
from website.models import HomePage, CareerAdvicePage, JobSearchPage, ProfilePage, BlogIndexPage
from wagtail.fields import StreamField
from profiles.models import Skill
from career.models import CareerPath, MarketInsight
from ai_engine.models import AIConfiguration

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up initial data for NextStep CMS'
    
    def handle(self, *args, **options):
        self.stdout.write('Setting up initial NextStep data...')
        
        # Get the root page
        root_page = Page.objects.get(title='Root')
        
        # Delete existing pages except root
        Page.objects.filter(depth__gt=1).delete()
        
        # Create home page
        home_page = HomePage(
            title='NextStep - AI Career Evolution',
            slug='home',
            hero_title='NextStep - Your AI-Powered Career Evolution Partner 🚀',
            hero_subtitle='Transform your professional journey with intelligent career guidance using cutting-edge AI technology.',
            hero_cta_text='Start Your Journey',
            hero_cta_url='/career-advice/',
            features_title='✨ Key Features',
            features_description='Empower your career with our comprehensive AI-driven platform'
        )
        
        root_page.add_child(instance=home_page)
        
        # Set as default site homepage
        site = Site.objects.get(is_default_site=True)
        site.root_page = home_page
        site.save()
        
        # Create career advice page
        career_advice_page = CareerAdvicePage(
            title='Career Advice',
            slug='career-advice',
            introduction='<p>Get personalized, AI-powered career advice tailored to your unique background and goals.</p>'
        )
        home_page.add_child(instance=career_advice_page)
        
        # Create job search page
        job_search_page = JobSearchPage(
            title='Job Search',
            slug='jobs',
            introduction='<p>Discover your perfect job with our AI-powered job matching and analysis platform.</p>',
            featured_industries='["Technology", "Healthcare", "Finance", "Marketing", "Engineering", "Data Science"]'
        )
        home_page.add_child(instance=job_search_page)
        
        # Create profile page
        profile_page = ProfilePage(
            title='My Profile',
            slug='profile',
            introduction='<p>Build your comprehensive professional profile to unlock personalized career recommendations.</p>'
        )
        home_page.add_child(instance=profile_page)
        
        # Create blog index page
        blog_index_page = BlogIndexPage(
            title='Career Insights',
            slug='blog',
            introduction='<p>Stay updated with the latest career insights, industry trends, and professional development tips.</p>'
        )
        home_page.add_child(instance=blog_index_page)
        
        # Create some skills
        skills_data = [
            ('Python', 'technical', 'Programming language popular in data science and web development'),
            ('JavaScript', 'technical', 'Essential language for web development'),
            ('React', 'technical', 'Popular JavaScript library for building user interfaces'),
            ('SQL', 'technical', 'Database query language'),
            ('Data Analysis', 'technical', 'Analyzing data to extract insights'),
            ('Machine Learning', 'technical', 'AI/ML algorithms and models'),
            ('Project Management', 'soft_skills', 'Planning and executing projects'),
            ('Communication', 'soft_skills', 'Effective written and verbal communication'),
            ('Leadership', 'soft_skills', 'Leading teams and initiatives'),
            ('Problem Solving', 'soft_skills', 'Analytical and creative problem resolution'),
            ('AWS', 'tool', 'Amazon Web Services cloud platform'),
            ('Docker', 'tool', 'Containerization platform'),
            ('Git', 'tool', 'Version control system'),
            ('Tableau', 'tool', 'Data visualization software'),
            ('Agile', 'framework', 'Agile development methodology'),
        ]
        
        for name, category, description in skills_data:
            Skill.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'description': description,
                    'popularity_score': 0.8
                }
            )
        
        # Create career paths
        career_paths_data = [
            {
                'name': 'Software Engineer',
                'slug': 'software-engineer',
                'description': 'Design, develop, and maintain software applications and systems',
                'industry': 'Technology',
                'field': 'Software Development',
                'level': 'mid',
                'typical_education': ['bachelors'],
                'required_skills': ['Python', 'JavaScript', 'Git', 'Problem Solving'],
                'preferred_skills': ['React', 'AWS', 'Docker'],
                'typical_experience': 2,
                'average_salary_min': 70000,
                'average_salary_max': 120000,
                'growth_outlook': 'high_growth',
                'demand_score': 0.9,
                'competition_score': 0.7,
                'satisfaction_score': 0.8
            },
            {
                'name': 'Data Scientist',
                'slug': 'data-scientist',
                'description': 'Extract insights from data using statistical analysis and machine learning',
                'industry': 'Technology',
                'field': 'Data Science',
                'level': 'mid',
                'typical_education': ['bachelors', 'masters'],
                'required_skills': ['Python', 'SQL', 'Data Analysis', 'Machine Learning'],
                'preferred_skills': ['Tableau', 'AWS'],
                'typical_experience': 3,
                'average_salary_min': 80000,
                'average_salary_max': 140000,
                'growth_outlook': 'high_growth',
                'demand_score': 0.95,
                'competition_score': 0.8,
                'satisfaction_score': 0.85
            }
        ]
        
        for path_data in career_paths_data:
            CareerPath.objects.get_or_create(
                slug=path_data['slug'],
                defaults=path_data
            )
        
        # Create AI configurations
        ai_configs = [
            {
                'name': 'Job Analysis Configuration',
                'description': 'Configuration for analyzing job postings',
                'config_type': 'job_analysis',
                'model_name': 'gpt-4',
                'temperature': 0.3,
                'max_tokens': 2000,
                'system_prompt': '''You are an expert job market analyst. Analyze job postings and extract structured information about requirements, skills, and characteristics. Respond in JSON format with detailed analysis.''',
                'user_prompt_template': 'Analyze this job posting: {job_description}',
                'available_variables': ['job_description', 'job_title', 'company_name'],
                'response_format': 'json',
                'is_active': True
            },
            {
                'name': 'Career Advice Configuration',
                'description': 'Configuration for providing career advice',
                'config_type': 'career_advice',
                'model_name': 'gpt-4',
                'temperature': 0.7,
                'max_tokens': 1500,
                'system_prompt': '''You are NextStep's expert career advisor. Provide personalized, actionable career advice based on the user's profile and questions. Be encouraging, practical, and forward-thinking.''',
                'user_prompt_template': 'User question: {query}\nUser context: {user_context}',
                'available_variables': ['query', 'user_context'],
                'response_format': 'text',
                'is_active': True
            }
        ]
        
        for config_data in ai_configs:
            AIConfiguration.objects.get_or_create(
                name=config_data['name'],
                defaults=config_data
            )
        
        # Create market insights
        insights_data = [
            {
                'insight_type': 'industry',
                'category': 'Technology',
                'title': 'Tech Industry Outlook 2025',
                'summary': 'The technology sector continues to show strong growth with AI/ML roles leading the demand.',
                'detailed_analysis': 'Artificial Intelligence and Machine Learning roles are experiencing unprecedented demand in 2025. Companies across all industries are investing heavily in AI capabilities.',
                'demand_trend': 'high_growth',
                'salary_trend': 'rapidly_increasing',
                'key_statistics': {'job_growth': '25%', 'avg_salary_increase': '15%'},
                'trending_skills': ['Python', 'Machine Learning', 'AI', 'Cloud Computing'],
                'confidence_score': 0.9
            }
        ]
        
        for insight_data in insights_data:
            MarketInsight.objects.get_or_create(
                title=insight_data['title'],
                defaults=insight_data
            )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up initial NextStep data!')
        )
        self.stdout.write('Created:')
        self.stdout.write('- Home page with navigation')
        self.stdout.write('- Career advice page')
        self.stdout.write('- Job search page')
        self.stdout.write('- Profile page')
        self.stdout.write('- Blog index page')
        self.stdout.write(f'- {len(skills_data)} skills')
        self.stdout.write(f'- {len(career_paths_data)} career paths')
        self.stdout.write(f'- {len(ai_configs)} AI configurations')
        self.stdout.write(f'- {len(insights_data)} market insights')
        self.stdout.write('')
        self.stdout.write('You can now start the server and visit the site!')