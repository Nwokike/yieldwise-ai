# YieldWise AI - Replit Project Documentation

## Project Overview

YieldWise AI is a comprehensive agricultural intelligence platform that empowers farmers with AI-driven insights for farm planning and plant disease diagnosis. The application has been completely rebuilt with modern architecture and best practices.

## Recent Changes (October 2025)

### Major Improvements

1. **AI Model Migration**
   - Migrated from Groq (Llama 3.1) to Google Gemini 2.5 Flash for all AI features
   - Single unified AI model for both farm planning and plant diagnosis
   - Enhanced prompt engineering for better agricultural insights

2. **Architecture Refactoring**
   - Implemented template inheritance with base.html
   - Separated all CSS into dedicated static files (landing.css, etc.)
   - Separated all JavaScript into modular files (landing.js, utils.js)
   - Clean, maintainable codebase following Flask best practices

3. **Database Enhancement**
   - Environment-based database switching (SQLite dev, PostgreSQL prod)
   - PostgreSQL/Neon support for production deployments
   - Proper connection handling and error management

4. **Documentation**
   - Professional README with comprehensive setup instructions
   - Detailed Oracle Cloud deployment guide (DEPLOYMENT.md)
   - Environment configuration examples

## Technology Stack

- **Backend**: Flask 3.1.2 (Python 3.11)
- **AI**: Google Gemini 2.5 Flash
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Frontend**: Jinja2, CSS3, Vanilla JavaScript
- **Production**: Gunicorn, Nginx

## Project Structure

```
yieldwise-ai/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── static/
│   ├── style.css         # Global styles
│   ├── css/
│   │   └── landing.css   # Landing page styles
│   └── js/
│       ├── utils.js      # Utility functions
│       └── landing.js    # Landing page logic
├── templates/
│   ├── base.html         # Base template
│   ├── index.html        # Landing page
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── dashboard.html    # User dashboard
│   └── ...
└── DEPLOYMENT.md         # Deployment guide
```

## Environment Setup

### Required Secrets (Add via Replit Secrets)

1. **GOOGLE_API_KEY** (Required)
   - Get from: https://aistudio.google.com/app/apikey
   - Used for all AI features (farm planning & diagnosis)

2. **SECRET_KEY** (Optional)
   - Flask secret key for session management
   - Auto-generated if not provided

3. **DATABASE_URL** (Production only)
   - PostgreSQL connection string
   - Example: `postgresql://user:pass@host:5432/db`

4. **DATABASE_ENV** (Optional)
   - Set to `development` (default) or `production`

## Running the Application

The workflow is already configured:
- **Name**: YieldWise AI Server
- **Command**: `python app.py`
- **Port**: 5000
- **Output**: Webview

## Key Features

1. **AI Farm Planner**
   - Location-aware crop recommendations
   - Detailed budget breakdowns
   - 90-day action plans
   - Profit projections and market strategies

2. **AI Plant Doctor**
   - Image-based disease diagnosis
   - Organic and chemical treatment recommendations
   - Prevention strategies

3. **Interactive Chat**
   - Follow-up questions on farm plans
   - Expert advice from AI agronomist

4. **Professional Tools**
   - PDF export of farm plans
   - Public showcase creation
   - User dashboard and history

## API Endpoints

- `POST /api/generate` - Generate farm plan
- `POST /api/diagnose` - Diagnose plant issues
- `POST /api/follow_up` - Chat about farm plans
- `POST /api/diagnose_follow_up` - Chat about diagnoses
- `GET /api/health` - Health check

## Database Schema

- **users** - User accounts
- **farm_plans** - Generated farm plans
- **diagnoses** - Plant diagnoses
- **chat_history** - Plan conversations
- **diagnoses_chat_history** - Diagnosis conversations

## User Preferences

- **AI Model**: Gemini 2.5 Flash only (no Groq)
- **Database**: SQLite for development, PostgreSQL for production
- **Templates**: Base template with inheritance
- **Static Files**: Separated CSS and JS
- **Deployment**: Oracle Cloud preferred

## Deployment

For production deployment:
1. Set `DATABASE_ENV=production`
2. Configure `DATABASE_URL` with PostgreSQL connection
3. Add `GOOGLE_API_KEY` to environment
4. Use Gunicorn for production server
5. Follow DEPLOYMENT.md for Oracle Cloud setup

## Maintenance Notes

- Database is auto-initialized on first run
- Static files are cached with 304 responses
- Rate limiting: 3 requests/day for AI features (configurable)
- File uploads limited to 16MB (configurable)

## Future Enhancements

Potential improvements:
- Redis caching for rate limiting
- Background job processing for PDFs
- Advanced analytics dashboard
- Mobile app integration
- Multi-language support

## Support

For issues or questions:
- Email: nwokikeonyeka@gmail.com
- GitHub: @Nwokike

---

*Last Updated: October 2025*
*Version: 3.0.0*
