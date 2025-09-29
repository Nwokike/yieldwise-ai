# YieldWise AI - Replit Setup

## Project Overview
YieldWise AI is an all-in-one platform for African farmers to plan profitable farms, diagnose plant diseases with photos, and build their agricultural business using AI. The platform combines expert agronomic advice with advanced AI technologies.

## Technology Stack
- **Backend**: Flask (Python)
- **Database**: SQLite 3
- **AI Integration**: LangChain with Groq API (Llama 3.1) & Google Gemini 1.5 Flash API
- **Frontend**: HTML5, CSS3, Vanilla JavaScript with Jinja2 templating
- **PDF Generation**: WeasyPrint
- **Authentication**: Flask-Login with Werkzeug password hashing
- **Security**: Flask-Limiter for rate limiting

## Features
- **AI Farm Planner**: Generate detailed business plans using Groq Llama 3.1
- **AI Plant Doctor**: Diagnose plant diseases using Google Gemini 1.5 Flash
- **User Management**: Complete registration and login system
- **Interactive Chat**: Follow-up questions for plans and diagnoses
- **PDF Export**: Professional PDF generation of farm plans
- **Shareable Showcases**: Public webpage generation for farm plans

## Environment Setup
The application requires two API keys for full functionality:
- `GROQ_API_KEY`: For farm planning features (Groq Llama 3.1)
- `GOOGLE_API_KEY`: For plant diagnosis features (Google Gemini 1.5 Flash)

The application will start without these keys but with limited functionality.

## Current Configuration
- **Host**: 0.0.0.0 (configured for Replit environment)
- **Port**: 5000 (required for Replit)
- **Debug Mode**: Enabled for development
- **Database**: SQLite database automatically initialized on first run

## Recent Changes (Setup for Replit)
- Configured Flask app to bind to 0.0.0.0:5000 for Replit compatibility
- Added graceful fallback handling for missing API keys
- Set up workflow to run the Flask application
- Ensured proper error handling for AI service unavailability

## Project Structure
```
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── yieldwise.db          # SQLite database (auto-generated)
├── static/               # Static assets (CSS, JS)
├── templates/            # HTML templates
└── README.md             # Original project documentation
```

## Deployment Notes
- Application is ready for production deployment
- Uses Gunicorn for production WSGI server
- Configured for autoscale deployment target
- No build step required (pure Python application)

## User Preferences
- Clean, professional interface
- Focus on African agricultural context
- Emphasis on practical, actionable AI-generated advice
- Mobile-responsive design for farmer accessibility