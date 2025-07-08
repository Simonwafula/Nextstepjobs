# NextStep - Your AI-Powered Career Evolution Partner 🚀

Transform your professional journey with NextStep - the intelligent career guidance platform that empowers students, graduates, and professionals to make informed career decisions using cutting-edge AI technology.

## ✨ Features

- 🔮 **Anonymous Career Search** - Get instant AI-powered career guidance without registration
- 👤 **Personalized Profiles** - Create detailed profiles for tailored career advice
- 📋 **Smart Job Analysis** - AI-powered analysis of job descriptions with match scoring
- 💡 **Career Advice Engine** - Personalized guidance based on your unique background
- 📊 **Market Insights** - Industry trends, salary data, and future opportunities
- 🔥 **Trending Topics** - Popular career questions and hot job roles for 2025
- 🎯 **Skills Development** - Personalized skill recommendations and learning paths
- 🌟 **Industry Intelligence** - Deep insights into career paths and growth opportunities

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
