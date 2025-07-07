# Nextstep - AI-Powered Career Advisory Platform

![Nextstep Logo](https://github.com/Simonwafula/Nextstepjobs/blob/main/Nextstep%20logo.jpeg)

## 🎯 Overview

Nextstep is a comprehensive AI-powered career advisory platform designed to empower individuals in their professional journey. The platform combines advanced job market analysis, personalized career guidance, and intelligent job matching to help users make informed career decisions.

## ✨ Key Features

### 🔍 **Job Intelligence & Analysis**
- **Smart Job Scraping**: Automated job collection from multiple sources (LinkedIn, Indeed, BrighterMonday)
- **AI-Powered Job Analysis**: Detailed breakdown of job requirements, qualifications, and company culture
- **Job-Profile Matching**: Intelligent matching between user profiles and job opportunities
- **Market Insights**: Real-time job market trends and salary analysis

### 👤 **Personalized Career Guidance**
- **User Profiling**: Comprehensive user profiles with skills, experience, and career interests
- **Career Path Recommendations**: AI-suggested career trajectories based on user background
- **Skills Gap Analysis**: Identification of missing skills for target roles
- **Anonymous Career Search**: Get career guidance without registration

### 🎓 **Educational Pathways**
- **Degree-to-Career Mapping**: Comprehensive mapping of academic programs to career opportunities
- **Skills Development Recommendations**: Personalized learning suggestions
- **Industry Insights**: In-depth analysis of different industry sectors

### 📊 **Advanced Analytics**
- **Job Market Analysis**: Trends, salary ranges, and growth opportunities
- **Skills Demand Tracking**: Most in-demand skills across industries
- **Company Analysis**: Insights into hiring patterns and company culture

## 🚀 Technology Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **MongoDB**: NoSQL database for flexible data storage
- **Motor**: Async MongoDB driver
- **Emergent Integrations**: AI/LLM integration capabilities
- **Beautiful Soup**: Web scraping for job data
- **Pydantic**: Data validation and serialization

### Frontend
- **React**: Modern JavaScript UI library
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client for API communication
- **React Router**: Client-side routing

### AI & Processing
- **OpenAI GPT Integration**: Advanced natural language processing
- **Custom Job Processing Pipeline**: Intelligent job data extraction and analysis
- **Real-time Data Processing**: Async job processing and analysis

## 📁 Project Structure

```
nextstep/
├── backend/                 # FastAPI backend application
│   ├── server.py           # Main API server with endpoints
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── App.js         # Main React application
│   │   └── App.css        # Application styles
│   ├── public/            # Static assets
│   └── package.json       # Node.js dependencies
├── processors/             # Job processing pipeline
│   ├── pipeline2.py       # Advanced job processing algorithms
│   └── models.py          # Data models and validation
├── scrapers/              # Web scraping modules
│   ├── base_scraper.py    # Base scraper class
│   ├── linkedin_scraper.py # LinkedIn job scraper
│   ├── indeed_scraper.py   # Indeed job scraper
│   └── brighter_monday_scraper.py # BrighterMonday scraper
├── models/                # Database models
│   ├── user.py           # User profile models
│   ├── job.py            # Job data models
│   └── career.py         # Career guidance models
├── api/                   # API route modules
│   └── routes/           # Organized API endpoints
├── advisory_engine/       # Career advisory algorithms
│   ├── career_matcher.py  # Job-profile matching
│   ├── skill_analyser.py  # Skills analysis
│   └── recommendation_engine.py # Career recommendations
└── jobmate/              # UI/UX reference templates
    ├── assets/           # CSS, JS, and image assets
    └── *.html           # HTML template pages
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 14+
- MongoDB
- OpenAI API Key (for AI features)

### Backend Setup
```bash
# Clone the repository
git clone https://github.com/Simonwafula/Nextstepjobs.git
cd Nextstepjobs

# Install Python dependencies
cd backend
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration:
# - MONGO_URL=mongodb://localhost:27017/nextstep
# - OPENAI_API_KEY=your_openai_api_key
# - ENVIRONMENT=production

# Start the backend server
uvicorn server:app --host 0.0.0.0 --port 8001
```

### Frontend Setup
```bash
# Install Node.js dependencies
cd frontend
yarn install

# Set up environment variables
cp .env.example .env
# Edit .env with your backend URL:
# REACT_APP_BACKEND_URL=https://your-domain.com/api

# Build for production
yarn build

# Or start development server
yarn start
```

### Database Setup
```bash
# MongoDB setup (Ubuntu/Debian)
sudo apt update
sudo apt install mongodb

# Start MongoDB
sudo systemctl start mongodb
sudo systemctl enable mongodb

# Create database and collections (automatic on first run)
```

## 🚀 Production Deployment (VPS)

### Using Nginx + PM2 (Recommended)

#### 1. Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install nginx python3-pip nodejs npm mongodb -y

# Install PM2 for process management
sudo npm install -g pm2

# Install yarn
sudo npm install -g yarn
```

#### 2. Application Deployment
```bash
# Clone and setup application
git clone https://github.com/Simonwafula/Nextstepjobs.git /var/www/nextstep
cd /var/www/nextstep

# Setup backend
cd backend
pip3 install -r requirements.txt

# Setup frontend
cd ../frontend
yarn install
yarn build

# Setup environment variables
sudo nano /var/www/nextstep/backend/.env
# Add your production configurations
```

#### 3. PM2 Configuration
```bash
# Create PM2 ecosystem file
sudo nano /var/www/nextstep/ecosystem.config.js
```

```javascript
module.exports = {
  apps: [
    {
      name: 'nextstep-api',
      script: 'uvicorn',
      args: 'server:app --host 0.0.0.0 --port 8001',
      cwd: '/var/www/nextstep/backend',
      instances: 'max',
      exec_mode: 'cluster',
      env: {
        NODE_ENV: 'production'
      }
    }
  ]
}
```

#### 4. Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/nextstep
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /var/www/nextstep/frontend/build;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

#### 5. SSL Configuration (Optional but Recommended)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal setup
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### 6. Start Services
```bash
# Enable and start services
sudo systemctl enable nginx mongodb
sudo systemctl start nginx mongodb

# Start application with PM2
cd /var/www/nextstep
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### Using Docker (Alternative)

```dockerfile
# Dockerfile for production
FROM node:16-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN yarn install
COPY frontend/ ./
RUN yarn build

FROM python:3.9-slim AS backend
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install -r requirements.txt
COPY backend/ ./
COPY --from=frontend-build /app/frontend/build ./static

EXPOSE 8001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

## 📊 API Documentation

### Core Endpoints

#### User Management
- `POST /api/profiles` - Create user profile
- `GET /api/profiles/{user_id}` - Get user profile
- `PUT /api/profiles/{user_id}` - Update user profile

#### Job Analysis
- `POST /api/analyze-job` - Analyze job description
- `POST /api/jobs/search` - Search processed jobs
- `POST /api/jobs/recommendations/{user_id}` - Get personalized recommendations

#### Career Guidance
- `POST /api/career-advice` - Get personalized career advice
- `POST /api/search` - Anonymous career search
- `GET /api/popular-topics` - Get trending career topics

#### Job Intelligence
- `POST /api/jobs/scrape` - Scrape jobs from multiple sources
- `POST /api/market/analysis` - Analyze job market trends
- `POST /api/analysis/skills-gap/{user_id}` - Skills gap analysis

#### Educational Pathways
- `GET /api/degree-programs` - Get degree-to-career mappings
- `POST /api/degree-career-search` - Search degree-related careers
- `GET /api/market-insights/{field}` - Get industry insights

## 🛠️ Environment Configuration

### Required Environment Variables

#### Backend (.env)
```bash
# Database
MONGO_URL=mongodb://localhost:27017/nextstep

# AI Integration
OPENAI_API_KEY=your_openai_api_key

# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your_secret_key

# CORS (for production)
ALLOWED_ORIGINS=https://your-domain.com
```

#### Frontend (.env)
```bash
# API Configuration
REACT_APP_BACKEND_URL=https://your-domain.com/api

# Application
NODE_ENV=production
```

## 📋 TODO - Unfinished Features

### High Priority
- [ ] **User Authentication & Authorization**
  - JWT token implementation
  - User registration/login system
  - Role-based access control (user, admin)
  - Password reset functionality

- [ ] **Enhanced Job Scraping**
  - Complete LinkedIn scraper integration
  - Add more job sources (Glassdoor, AngelList)
  - Implement rate limiting and proxy rotation
  - Real-time job alerts via email/SMS

- [ ] **Advanced Analytics Dashboard**
  - Real-time job market analytics
  - Personal career progress tracking
  - Industry trend visualizations
  - Salary comparison tools

### Medium Priority
- [ ] **Resume Management**
  - Resume upload and parsing
  - AI-powered resume optimization
  - Multiple resume versions
  - Resume-job matching score

- [ ] **Company Intelligence**
  - Company profile database
  - Employee reviews integration
  - Company culture analysis
  - Hiring pattern insights

- [ ] **Networking Features**
  - Professional networking recommendations
  - Mentor-mentee matching
  - Industry expert connections
  - Career events and webinars

### Low Priority
- [ ] **Mobile Application**
  - React Native mobile app
  - Push notifications
  - Offline functionality
  - Mobile-optimized UI

- [ ] **Advanced AI Features**
  - Interview question generation
  - Salary negotiation guidance
  - Career path simulation
  - Personality-based recommendations

- [ ] **Integration & APIs**
  - LinkedIn API integration
  - Google Calendar integration
  - Slack/Teams bot
  - Third-party ATS integration

### Infrastructure & DevOps
- [ ] **Monitoring & Logging**
  - Application performance monitoring
  - Error tracking and alerting
  - User analytics and insights
  - Server health monitoring

- [ ] **Security Enhancements**
  - API rate limiting
  - Input validation and sanitization
  - Security headers implementation
  - Regular security audits

- [ ] **Scalability Improvements**
  - Database optimization and indexing
  - Caching layer implementation
  - Load balancing setup
  - Microservices architecture

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