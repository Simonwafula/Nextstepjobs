# Career Navigator - AI-Powered Career Advisor

Your intelligent career guidance platform that helps students, graduates, and professionals make informed career decisions using AI.

## Features

- 🔍 **Anonymous Career Search** - Get instant career guidance without registration
- 👤 **Personalized Profiles** - Create detailed profiles for tailored advice
- 📋 **Job Analysis** - AI-powered analysis of job descriptions
- 💡 **Career Advice** - Personalized guidance based on your background
- 📊 **Market Insights** - Industry trends and opportunities
- 🔥 **Trending Topics** - Popular career questions and hot job roles

## Environment Setup

### Backend Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in your values:

```bash
cp backend/.env.example backend/.env
```

Required variables:
- `MONGO_URL` - MongoDB connection string
- `DB_NAME` - Database name
- `OPENAI_API_KEY` - Your OpenAI API key (get from https://platform.openai.com/api-keys)

### Frontend Environment Variables

Copy `frontend/.env.example` to `frontend/.env` and fill in your values:

```bash
cp frontend/.env.example frontend/.env
```

Required variables:
- `REACT_APP_BACKEND_URL` - Your backend API URL
- `WDS_SOCKET_PORT` - WebSocket port for development

## Security

⚠️ **Important**: Never commit `.env` files to version control. They contain sensitive information like API keys.

The `.env` files are already included in `.gitignore` to prevent accidental commits.