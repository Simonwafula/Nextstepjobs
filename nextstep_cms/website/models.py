from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.blocks import CharBlock, TextBlock, StructBlock, StreamBlock, FieldBlock
from coderedcms.models import CoderedPage, CoderedWebPage
from coderedcms.blocks import BaseBlock, BaseLayoutBlock


class CareerAdviceBlock(BaseBlock):
    """Custom block for career advice functionality"""
    
    title = CharBlock(max_length=255, required=False, help_text="Title for the career advice section")
    description = TextBlock(required=False, help_text="Description of the career advice feature")
    
    class Meta:
        template = "website/blocks/career_advice_block.html"
        icon = "help"
        label = "Career Advice"


class JobSearchBlock(BaseBlock):
    """Custom block for job search functionality"""
    
    title = CharBlock(max_length=255, required=False, help_text="Title for the job search section")
    description = TextBlock(required=False, help_text="Description of the job search feature")
    featured_industries = CharBlock(max_length=500, required=False, help_text="Comma-separated list of featured industries")
    
    class Meta:
        template = "website/blocks/job_search_block.html"
        icon = "search"
        label = "Job Search"


class ProfileBuilderBlock(BaseBlock):
    """Custom block for profile building functionality"""
    
    title = CharBlock(max_length=255, required=False, help_text="Title for the profile builder section")
    description = TextBlock(required=False, help_text="Description of the profile building feature")
    
    class Meta:
        template = "website/blocks/profile_builder_block.html"
        icon = "user"
        label = "Profile Builder"


class AIAnalysisBlock(BaseBlock):
    """Custom block for AI job analysis functionality"""
    
    title = CharBlock(max_length=255, required=False, help_text="Title for the AI analysis section")
    description = TextBlock(required=False, help_text="Description of the AI analysis feature")
    
    class Meta:
        template = "website/blocks/ai_analysis_block.html"
        icon = "cogs"
        label = "AI Analysis"


class NextStepStreamBlock(StreamBlock):
    """Custom stream block for NextStep pages"""
    
    career_advice = CareerAdviceBlock()
    job_search = JobSearchBlock()
    profile_builder = ProfileBuilderBlock()
    ai_analysis = AIAnalysisBlock()


class HomePage(CoderedWebPage):
    """Home page for NextStep"""
    
    template = "website/pages/home_page.html"
    
    # Hero Section
    hero_title = models.CharField(max_length=255, default="NextStep - Your AI-Powered Career Evolution Partner")
    hero_subtitle = models.TextField(default="Transform your professional journey with intelligent career guidance using cutting-edge AI technology.")
    hero_cta_text = models.CharField(max_length=100, default="Start Your Journey")
    hero_cta_url = models.URLField(blank=True, default="/career-advice/")
    
    # Features Section
    features_title = models.CharField(max_length=255, default="✨ Key Features")
    features_description = models.TextField(default="Empower your career with our comprehensive AI-driven platform")
    
    # Content areas
    body = StreamField(NextStepStreamBlock(), blank=True, use_json_field=True)
    
    content_panels = CoderedWebPage.content_panels + [
        MultiFieldPanel([
            FieldPanel('hero_title'),
            FieldPanel('hero_subtitle'),
            FieldPanel('hero_cta_text'),
            FieldPanel('hero_cta_url'),
        ], heading="Hero Section"),
        MultiFieldPanel([
            FieldPanel('features_title'),
            FieldPanel('features_description'),
        ], heading="Features Section"),
        FieldPanel('body'),
    ]
    
    class Meta:
        verbose_name = "Home Page"


class CareerAdvicePage(CoderedWebPage):
    """Page for career advice functionality"""
    
    template = "website/pages/career_advice_page.html"
    
    introduction = RichTextField(
        default="Get personalized, AI-powered career advice tailored to your unique background and goals."
    )
    
    content_panels = CoderedWebPage.content_panels + [
        FieldPanel('introduction'),
    ]
    
    class Meta:
        verbose_name = "Career Advice Page"


class JobSearchPage(CoderedWebPage):
    """Page for job search functionality"""
    
    template = "website/pages/job_search_page.html"
    
    introduction = RichTextField(
        default="Discover your perfect job with our AI-powered job matching and analysis platform."
    )
    featured_industries = models.TextField(
        blank=True,
        help_text="JSON list of featured industries",
        default='["Technology", "Healthcare", "Finance", "Marketing", "Engineering"]'
    )
    
    content_panels = CoderedWebPage.content_panels + [
        FieldPanel('introduction'),
        FieldPanel('featured_industries'),
    ]
    
    class Meta:
        verbose_name = "Job Search Page"


class ProfilePage(CoderedWebPage):
    """Page for user profile management"""
    
    template = "website/pages/profile_page.html"
    
    introduction = RichTextField(
        default="Build your comprehensive professional profile to unlock personalized career recommendations."
    )
    
    content_panels = CoderedWebPage.content_panels + [
        FieldPanel('introduction'),
    ]
    
    class Meta:
        verbose_name = "Profile Page"


class BlogPage(CoderedWebPage):
    """Blog page for career-related articles"""
    
    template = "website/pages/blog_page.html"
    
    excerpt = models.TextField(max_length=500, blank=True)
    featured_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    author = models.CharField(max_length=255, default="NextStep Team")
    read_time = models.PositiveIntegerField(default=5, help_text="Estimated read time in minutes")
    
    # Article content
    article_body = RichTextField()
    
    # SEO and categorization
    category = models.CharField(
        max_length=100,
        choices=[
            ('career_advice', 'Career Advice'),
            ('industry_insights', 'Industry Insights'),
            ('skill_development', 'Skill Development'),
            ('job_search', 'Job Search Tips'),
            ('salary_negotiation', 'Salary Negotiation'),
            ('interview_prep', 'Interview Preparation'),
        ],
        default='career_advice'
    )
    article_tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    
    content_panels = CoderedWebPage.content_panels + [
        FieldPanel('excerpt'),
        FieldPanel('featured_image'),
        FieldPanel('author'),
        FieldPanel('read_time'),
        FieldPanel('category'),
        FieldPanel('article_tags'),
        FieldPanel('article_body'),
    ]
    
    class Meta:
        verbose_name = "Blog Article"
        verbose_name_plural = "Blog Articles"


class BlogIndexPage(CoderedWebPage):
    """Index page for blog articles"""
    
    template = "website/pages/blog_index_page.html"
    
    introduction = RichTextField(
        default="Stay updated with the latest career insights, industry trends, and professional development tips."
    )
    
    content_panels = CoderedWebPage.content_panels + [
        FieldPanel('introduction'),
    ]
    
    def get_context(self, request):
        context = super().get_context(request)
        
        # Get all blog pages
        blog_pages = BlogPage.objects.live().public().order_by('-first_published_at')
        
        # Filter by category if specified
        category = request.GET.get('category')
        if category:
            blog_pages = blog_pages.filter(category=category)
        
        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(blog_pages, 10)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context['blog_pages'] = page_obj
        context['categories'] = [
            ('career_advice', 'Career Advice'),
            ('industry_insights', 'Industry Insights'),
            ('skill_development', 'Skill Development'),
            ('job_search', 'Job Search Tips'),
            ('salary_negotiation', 'Salary Negotiation'),
            ('interview_prep', 'Interview Preparation'),
        ]
        context['current_category'] = category
        
        return context
    
    class Meta:
        verbose_name = "Blog Index Page"


class CareerGuide(models.Model):
    """Career guides and resources"""
    
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    content = RichTextField()
    
    # Categorization
    category = models.CharField(
        max_length=100,
        choices=[
            ('career_paths', 'Career Paths'),
            ('skill_guides', 'Skill Development Guides'),
            ('industry_guides', 'Industry Guides'),
            ('education_guides', 'Education Guides'),
            ('job_search_guides', 'Job Search Guides'),
        ]
    )
    
    # Metadata
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='beginner'
    )
    estimated_read_time = models.PositiveIntegerField(default=10, help_text="Minutes")
    
    # SEO
    featured_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class TrendingTopic(models.Model):
    """Trending career topics for the homepage"""
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    icon = models.CharField(max_length=50, default="💼")
    link_url = models.URLField(blank=True)
    
    # Display settings
    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return self.title