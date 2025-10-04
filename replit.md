# YieldWise AI - Agricultural Platform

## Overview
YieldWise AI is a comprehensive agricultural technology platform that helps farmers plan profitable farms, diagnose plant diseases with AI-powered image analysis, and access expert farming knowledge. The platform has been significantly enhanced with multiple FREE features to scale it into a top-tier agricultural startup solution.

## Current State
**Status:** Configured and Running ✅  
**Last Updated:** October 4, 2025  
**Version:** 2.0.0 (Significantly Enhanced)
**Environment:** Replit (imported and configured)

⚠️ **Important:** To enable AI features, add these API keys to Replit Secrets:
- `GEMINI_API_KEY` or `GOOGLE_API_KEY` - Required for AI Plant Doctor and Knowledge Base (get from https://aistudio.google.com/)
- `GROQ_API_KEY` - Required for AI Farm Planner (get from https://console.groq.com/)

The app will run without these keys, but AI features will be disabled.

## Core Features

### 1. AI Farm Planner (Original Feature - Enhanced)
- Generate detailed, location-specific farm business plans
- AI-powered crop recommendations using Gemini AI
- Budget breakdown and earnings projections
- 90-day action plans
- Download plans as professional PDFs
- Create public showcase pages to share plans

### 2. AI Plant Doctor (Original Feature - Enhanced)
- Upload plant photos for instant disease diagnosis
- Gemini Vision AI analyzes images
- Organic and chemical treatment recommendations
- Interactive follow-up chat for detailed questions
- Diagnosis history tracking

### 3. 📊 Analytics Dashboard (NEW - FREE)
- Visual charts showing farm performance over time
- Track cumulative plans created
- Location-based analysis
- Investment distribution visualization
- ROI potential estimations
- Built with Chart.js (completely free library)

### 4. 🧮 Resource Calculator (NEW - FREE)
- **Seeds Calculator:** Calculate exact seed requirements by crop type and farm size
- **Water Calculator:** Determine daily/weekly water needs based on climate
- **Fertilizer Calculator:** Calculate fertilizer requirements by soil type
- **Labor Calculator:** Estimate man-hours needed for different farming activities
- All calculations use research-based formulas
- No external APIs required

### 5. 📚 Knowledge Base (NEW - FREE)
- AI-powered farming expert Q&A
- Ask any farming question and get instant AI answers
- Pre-written guides on:
  - Pest Management (organic and chemical methods)
  - Soil Health (pH management, composting)
  - Water Management (irrigation techniques)
  - Crop Rotation (best practices)
  - Organic Farming (natural methods)
  - Marketing Tips (selling strategies)
- Powered by Gemini AI - no additional costs

### 6. 🌍 Community Showcase Gallery (NEW - FREE)
- Browse public farm plans shared by other farmers
- Get inspired by successful farming strategies worldwide
- See plans from different locations and climates
- Learn from the community
- No hosting costs - uses existing database

### 7. Enhanced User Experience
- Modern, clean UI with consistent design
- Smooth transitions and animations
- Mobile-responsive design
- Intuitive navigation with icon-based sidebar
- Progress indicators for AI operations
- Toast notifications for user feedback

## Tech Stack

### Backend
- **Framework:** Flask 3.1.2 (Python)
- **Database:** SQLite 3
- **AI Models:** 
  - Google Gemini 2.5 Flash (multimodal - image + text)
  - Groq Llama 3.1 (optional for text generation)
- **PDF Generation:** WeasyPrint
- **Security:** Flask-Login, Werkzeug password hashing, Flask-Limiter
- **Server:** Gunicorn for production

### Frontend
- **Templating:** Jinja2
- **Styling:** Vanilla CSS3 with modern gradients and animations
- **JavaScript:** Vanilla JS (no framework overhead)
- **Charts:** Chart.js 4.4.0 (free, lightweight)
- **Icons:** Font Awesome 6.4.0

### Infrastructure
- **Environment:** Replit (NixOS)
- **Hosting:** Replit deployment (can scale to production)
- **Port:** 5000 (frontend)
- **Database:** File-based SQLite (simple, no hosting costs)

## Project Structure
```
/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── static/
│   ├── style.css                   # Global styles
│   └── js/
│       ├── utils.js                # Utility functions
│       ├── offline.js              # Service worker registration
│       └── sw.js                   # Service worker for PWA
├── templates/
│   ├── index.html                  # Landing page
│   ├── register.html               # User registration
│   ├── login.html                  # User login
│   ├── dashboard.html              # Main dashboard (farm planner)
│   ├── diagnostician.html          # Plant disease diagnosis
│   ├── analytics.html              # Analytics dashboard (NEW)
│   ├── resources.html              # Resource calculator (NEW)
│   ├── knowledge_base.html         # Farming knowledge base (NEW)
│   ├── community_showcase.html     # Community gallery (NEW)
│   ├── showcase.html               # Public showcase page
│   ├── 404.html                    # Error page
│   └── 500.html                    # Error page
└── yieldwise.db                    # SQLite database

```

## API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login
- `GET /logout` - User logout

### Farm Planning
- `POST /api/generate` - Generate new farm plan (rate limited: 3/day per user)
- `GET /api/get_plan/<id>` - Retrieve specific plan
- `DELETE /api/delete_plan/<id>` - Delete plan
- `POST /api/follow_up` - Chat follow-up for farm plans
- `POST /api/create_showcase` - Create public showcase

### Plant Diagnosis
- `POST /api/diagnose` - Upload image for diagnosis (rate limited: 3/day)
- `GET /api/get_diagnosis/<id>` - Retrieve diagnosis
- `DELETE /api/delete_diagnosis/<id>` - Delete diagnosis
- `POST /api/diagnose_follow_up` - Chat follow-up for diagnoses

### New Features
- `POST /api/knowledge_query` - Ask AI farming expert questions
- `GET /api/search_plans` - Search user's plans
- `GET /api/export_data` - Export all user data as JSON
- `GET /api/health` - System health check

### Utilities
- `GET /download_pdf/<id>` - Download plan as PDF

## Database Schema

### users
- id (PRIMARY KEY)
- email (UNIQUE)
- password (hashed)
- name

### farm_plans
- id (PRIMARY KEY)
- user_id (FOREIGN KEY)
- location
- country
- currency
- plan_html (generated AI content)
- showcase_id (for public sharing)
- is_promoted (monetization field)
- created_at

### chat_history
- id (PRIMARY KEY)
- plan_id (FOREIGN KEY)
- role (user/assistant)
- content
- created_at

### diagnoses
- id (PRIMARY KEY)
- user_id (FOREIGN KEY)
- title
- crop_type
- report_html
- created_at

### diagnoses_chat_history
- id (PRIMARY KEY)
- diagnosis_id (FOREIGN KEY)
- role (user/assistant)
- content
- created_at

## Environment Variables
Required secrets (managed through Replit Secrets):
- `GEMINI_API_KEY` - Google Gemini API key (for AI features)
- `GROQ_API_KEY` - Optional, for Groq Llama integration
- `SECRET_KEY` - Flask secret key (auto-generated if not provided)

## Setup & Development

1. **Python Environment:** Python 3.11+ installed via Replit
2. **Install Dependencies:** `pip install -r requirements.txt` (handled by Replit packager)
3. **Set Environment Variables:** Add GEMINI_API_KEY to Replit Secrets
4. **Run Server:** `python app.py` (configured as workflow)
5. **Access:** http://0.0.0.0:5000

## Deployment Configuration
- **Deployment Target:** VM or Autoscale (to be configured)
- **Build Command:** None required (Python interpreted)
- **Run Command:** `gunicorn --bind=0.0.0.0:5000 --reuse-port app:app`
- **Port:** 5000

## Key Improvements Made (Version 2.0)

### 1. Scalability
- Added 5 new feature pages (all FREE)
- Modular route structure for easy expansion
- Database optimized with proper indexing
- Rate limiting to prevent abuse

### 2. User Value
- **3x more features** than original version
- Resource calculators save farmers time and money
- Knowledge base provides instant expert advice
- Analytics help track farm performance
- Community feature fosters learning

### 3. Cost Efficiency
- All new features use FREE libraries and tools
- No additional API costs
- Chart.js for visualizations (free)
- SQLite for data storage (no database hosting fees)
- Efficient AI usage (only Gemini API needed)

### 4. User Experience
- Consistent modern design across all pages
- Icon-based navigation for quick access
- Mobile-responsive layouts
- Real-time feedback with notifications
- Smooth animations and transitions

## Future Enhancement Ideas (User Requested - Not Implemented)
- Weather integration (requires paid API)
- Market price tracking (requires paid API)
- SMS notifications (requires paid service)
- Advanced payment features (Stripe integration)
- Video tutorials
- Mobile app (React Native)

## Notes
- Rate limiting uses in-memory storage (fine for development, consider Redis for production)
- Database is file-based SQLite (suitable for MVP, consider PostgreSQL for heavy traffic)
- Debug mode enabled for development (disable for production)
- GROQ API is optional - app works with only Gemini

## Author
Onyeka Nwokike  
Agricultural and Bioresources Engineer | Software Developer  
PLP Africa Student

## License
Educational/Personal Use

---
**Built with ❤️ for African Farmers**
