# NextStep - Your AI-Powered Career Evolution Partner 🚀

Transform your professional journey with NextStep - the intelligent career guidance platform that empowers students, graduates, and professionals to make informed career decisions using cutting-edge AI technology.

**Now powered by Django + Wagtail CRX for enterprise-grade content management and scalability!**

## ✨ Key Features

### 🔮 **Anonymous Career Search**
Get instant AI-powered career guidance without registration - perfect for quick career exploration and advice.

### 👤 **Comprehensive User Profiles**
Create detailed profiles with skills, experience, education, and career goals for personalized recommendations.

### 📋 **AI-Powered Job Analysis**
Advanced job description analysis with requirement extraction, match scoring, and improvement recommendations.

### 💡 **Intelligent Career Advice Engine**
Personalized guidance based on your unique background, goals, and market trends.

### 📊 **Real-Time Market Insights**
Industry trends, salary data, skills demand, and future opportunities across sectors.

### 🎯 **Skills Development Recommendations**
Personalized skill gap analysis and learning path suggestions.

### 🏢 **Job Intelligence & Matching**
Smart job scraping, processing, and matching with AI-powered compatibility scoring.

### 📝 **Rich Content Management**
Blog articles, career guides, industry insights, and trending topics managed through Wagtail CRX.

## 🏗️ Architecture Overview

NextStep is built on a modern, scalable architecture:

- **Backend**: Django + Wagtail CRX for robust content management and APIs
- **Database**: PostgreSQL for relational data with SQLite fallback for development
- **AI Integration**: Advanced AI capabilities using Emergent Integrations
- **Background Processing**: Celery for job scraping and analysis tasks
- **Frontend**: Wagtail CRX with interactive React components
- **APIs**: Django REST Framework for comprehensive API access

## 🚀 Technology Stack

### Backend Framework
- **Django 5.2+**: Robust Python web framework
- **Wagtail CRX (CodeRedCMS)**: Enterprise content management system
- **Django REST Framework**: Comprehensive API development
- **PostgreSQL**: Production-ready relational database
- **Celery**: Distributed task queue for background processing

### Frontend & UI
- **Wagtail CRX**: Rich content management interface
- **React Components**: Interactive career tools and widgets
- **Tailwind CSS**: Modern utility-first CSS framework
- **Progressive Enhancement**: Works with and without JavaScript

### AI & Processing
- **Emergent Integrations**: Advanced AI/LLM integration
- **OpenAI GPT-4**: Natural language processing and analysis
- **Background Task Processing**: Async job analysis and matching
- **Real-time Career Guidance**: Instant AI-powered advice

### Database & Storage
- **PostgreSQL**: Primary database for production
- **SQLite**: Development database
- **UUID Primary Keys**: Distributed-system ready
- **JSON Fields**: Flexible data storage for skills and preferences

## 📁 Project Structure

```
nextstep_cms/
├── nextstep_cms/              # Django project settings
│   ├── settings/
│   │   ├── base.py           # Base settings
│   │   └── dev.py            # Development settings
│   ├── urls.py               # Main URL configuration
│   └── celery.py             # Celery configuration
├── website/                   # Wagtail CRX website app
│   ├── models.py             # Page models and content types
│   ├── templates/            # Wagtail templates
│   │   ├── pages/           # Page templates
│   │   └── blocks/          # Custom block templates
│   └── management/          # Django management commands
├── profiles/                  # User profile management
│   ├── models.py            # Profile, skills, experience models
│   └── api/                 # Profile API endpoints
├── jobs/                     # Job management system
│   ├── models.py            # Job, company, matching models
│   ├── tasks.py             # Celery background tasks
│   └── api/                 # Job API endpoints
├── career/                   # Career guidance engine
│   ├── models.py            # Career paths, advice, goals
│   └── api/                 # Career guidance APIs
├── ai_engine/                # AI processing and analytics
│   ├── models.py            # AI configurations and analytics
│   └── api/                 # AI processing endpoints
└── requirements.txt          # Python dependencies
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 13+ (optional - SQLite works for development)
- Redis (optional - for production Celery/caching)
- OpenAI API Key (for AI features)

### Quick Start (Development)

```bash
# Clone the repository
git clone https://github.com/Simonwafula/Nextstepjobs.git
cd Nextstepjobs/nextstep_cms

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration:
# - OPENAI_API_KEY=your_openai_api_key
# - DEBUG=True
# - DB_NAME=nextstep_db.sqlite3 (for SQLite development)

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Setup initial data
python manage.py setup_initial_data

# Start development server
python manage.py runserver 0.0.0.0:8001
```

### Production Setup (PostgreSQL)

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb nextstep_db
sudo -u postgres createuser nextstep_user
sudo -u postgres psql -c "ALTER USER nextstep_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE nextstep_db TO nextstep_user;"

# Update .env for production
DB_NAME=nextstep_db
DB_USER=nextstep_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DEBUG=False

# Run production migrations
python manage.py migrate
python manage.py collectstatic --noinput
```

### Celery Setup (Background Tasks)

```bash
# Install and start Redis
sudo apt install redis-server
sudo systemctl start redis-server

# Start Celery worker (in separate terminal)
celery -A nextstep_cms worker --loglevel=info

# Start Celery beat (for scheduled tasks)
celery -A nextstep_cms beat --loglevel=info
```

## 🌐 Access Points

After starting the server, you can access:

- **Main Website**: http://localhost:8001/
- **Wagtail Admin**: http://localhost:8001/admin/ (superuser login)
- **Django Admin**: http://localhost:8001/django-admin/
- **API Documentation**: http://localhost:8001/api/
- **Career Advice**: http://localhost:8001/career-advice/
- **Job Search**: http://localhost:8001/jobs/
- **Profile Builder**: http://localhost:8001/profile/

## 📊 API Documentation

### Core API Endpoints

#### User Profile Management
```bash
# Create user profile
POST /api/profiles/
{
  "name": "John Doe",
  "email": "john@example.com",
  "education_level": "bachelors",
  "experience_years": 3,
  "current_role": "Software Engineer"
}

# Get user profile
GET /api/profiles/{profile_id}/

# Update user profile
PUT /api/profiles/{profile_id}/
```

#### Career Guidance
```bash
# Get AI career advice
POST /api/career-advice/
{
  "user_id": "uuid",
  "query": "How do I transition from marketing to data science?",
  "session_type": "career_change"
}

# Anonymous career search
POST /api/anonymous-search/
{
  "query": "What skills do I need for AI engineering?",
  "search_type": "skills"
}
```

#### Job Analysis
```bash
# Analyze job description
POST /api/analyze-job/
{
  "user_id": "uuid",
  "job_description": "...",
  "job_title": "Senior Data Scientist",
  "company_name": "Tech Corp"
}

# Search jobs
POST /api/jobs/search/
{
  "keywords": ["python", "data science"],
  "location": "San Francisco",
  "experience_level": "mid",
  "remote_only": false
}
```

#### Skills & Career Development
```bash
# Skill gap analysis
POST /api/skill-gap-analysis/
{
  "user_id": "uuid",
  "target_roles": ["Data Scientist", "ML Engineer"]
}

# Get career recommendations
GET /api/career-recommendations/{user_id}/
```

## 🛠️ Environment Configuration

### Backend Environment Variables (.env)

```bash
# Database (PostgreSQL)
DB_NAME=nextstep_db
DB_USER=nextstep_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Database (SQLite for development)
# DB_NAME=nextstep_db.sqlite3

# AI Integration
OPENAI_API_KEY=your_openai_api_key

# Celery (Production)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Cache (Production)
REDIS_URL=redis://127.0.0.1:6379/1

# Django
DEBUG=False
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=your-domain.com,localhost
```

## 🚀 Production Deployment

### Using Docker (Recommended)

```dockerfile
# Docker deployment
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8001
CMD ["gunicorn", "nextstep_cms.wsgi:application", "--bind", "0.0.0.0:8001"]
```

### Using Nginx + Gunicorn

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /path/to/nextstep_cms/static/;
    }

    location /media/ {
        alias /path/to/nextstep_cms/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🎨 Content Management

### Wagtail CRX Features

- **Rich Page Editor**: Visual page building with custom blocks
- **Blog Management**: Complete blogging system for career content
- **SEO Optimization**: Built-in SEO tools and meta management
- **User Management**: Role-based access control
- **Form Builder**: Custom forms for user engagement
- **Analytics**: Integrated analytics and reporting

### Custom Blocks Available

- **Career Advice Block**: Interactive AI career guidance widget
- **Job Search Block**: Advanced job search with filtering
- **Profile Builder Block**: User profile creation interface
- **AI Analysis Block**: Job description analysis tool

## 📈 Background Tasks

### Celery Tasks

- **Job Scraping**: Automated job collection from multiple sources
- **AI Processing**: Background job analysis and processing
- **User Matching**: Calculate job-user compatibility scores
- **Data Cleanup**: Regular maintenance and optimization tasks

## 🔒 Security Features

- **CSRF Protection**: Built-in Django CSRF protection
- **SQL Injection Prevention**: Django ORM protection
- **XSS Protection**: Template auto-escaping
- **Authentication**: Session-based authentication
- **Permission System**: Django's robust permission framework

## 📋 Migration Notes

This version represents a complete architectural migration from:
- **FastAPI** → **Django + Wagtail CRX**
- **MongoDB** → **PostgreSQL**
- **Basic React SPA** → **Wagtail CRX with React blocks**
- **Manual processing** → **Celery background tasks**

All previous functionality has been preserved and enhanced with enterprise-grade features.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support, email support@nextstep.co.ke or join our Slack channel.

## 🙏 Acknowledgments

- Django and Wagtail communities for excellent frameworks
- CodeRed Corp for Wagtail CRX
- OpenAI for GPT integration capabilities
- The open-source community for various tools and libraries

---

**Built with ❤️ by the NextStep Team**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support, email support@nextstep.co.ke or join our Slack channel.

## 🙏 Acknowledgments

- OpenAI for GPT integration capabilities
- The open-source community for various tools and libraries
- Beta testers and early adopters for valuable feedback

---

**Built with ❤️ by the Nextstep Team**