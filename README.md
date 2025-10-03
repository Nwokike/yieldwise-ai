# 🌱 YieldWise AI

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.1-black?style=for-the-badge&logo=flask)
![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-4285F4?style=for-the-badge&logo=google)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**AI-Powered Agricultural Planning & Plant Diagnosis Platform**

Transform your farming business with cutting-edge AI technology powered by Google's Gemini 2.5 Flash

[Live Demo](#) • [Documentation](#getting-started) • [API Reference](#)

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

YieldWise AI is a comprehensive agricultural intelligence platform designed to empower farmers, agronomists, and agricultural entrepreneurs with AI-driven insights. Built with Google's latest Gemini 2.5 Flash model, the platform provides:

- **Intelligent Farm Planning** - Generate complete business plans with crop recommendations, budget breakdowns, and profit projections
- **AI Plant Diagnostics** - Upload plant images to diagnose diseases and receive treatment recommendations
- **Interactive Consultation** - Ask follow-up questions and get expert advice on your plans and diagnoses
- **Professional Reports** - Export plans as PDF documents and create shareable showcases

### Problem Statement

Smallholder farmers globally face critical challenges:
- Limited access to expert agronomic advice
- High costs of professional farm planning and soil testing
- Devastating crop losses from undiagnosed diseases
- Information gaps affecting food security and economic growth

YieldWise AI addresses these challenges by democratizing access to agricultural expertise through AI.

---

## ✨ Key Features

### 🌾 AI Farm Planner
- **Comprehensive Business Plans**: Location-aware crop recommendations with detailed implementation strategies
- **Budget Optimization**: Precise cost breakdowns for seeds, fertilizer, tools, and operational expenses
- **Profit Projections**: Realistic revenue and earnings estimates based on local market data
- **Risk Management**: Identification of potential risks with mitigation strategies
- **Market Intelligence**: Best practices for local and online selling

### 🔬 AI Plant Doctor
- **Visual Diagnosis**: Advanced image analysis to identify diseases, pests, and deficiencies
- **Treatment Options**: Both organic and chemical treatment recommendations
- **Prevention Strategies**: Proactive measures to maintain plant health
- **Confidence Scoring**: AI provides confidence levels for diagnoses

### 💬 Interactive AI Chat
- **Contextual Conversations**: Ask follow-up questions about your farm plans
- **Expert Knowledge**: Get detailed answers from AI agricultural experts
- **Conversation History**: Track all interactions for future reference

### 📊 Professional Tools
- **PDF Export**: Download professionally formatted farm plans
- **Public Showcases**: Create shareable links for your farm plans
- **Dashboard Analytics**: Track all your plans and diagnoses
- **User Management**: Secure authentication and data privacy

---

## 🛠 Technology Stack

### Backend
- **Framework**: Flask 3.1.2 (Python)
- **AI Engine**: Google Gemini 2.5 Flash (multimodal AI)
- **Database**: 
  - SQLite (Development)
  - PostgreSQL/Neon (Production)
- **Authentication**: Flask-Login with secure password hashing
- **Security**: Flask-Limiter for rate limiting, CSRF protection

### Frontend
- **Templating**: Jinja2 with template inheritance
- **Styling**: Modern CSS3 with responsive design
- **JavaScript**: Vanilla JS with utility classes
- **Icons**: Font Awesome 6

### Infrastructure
- **PDF Generation**: WeasyPrint
- **Image Processing**: Pillow (PIL)
- **Environment Management**: python-dotenv
- **Production Server**: Gunicorn

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- pip package manager
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/yieldwise-ai.git
cd yieldwise-ai
```

2. **Create a virtual environment** (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Create a `.env` file in the root directory:
```env
# Required: Google Gemini API Key
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional: Custom secret key
SECRET_KEY=your_secret_key_here

# Database Configuration
DATABASE_ENV=development  # Use 'production' with DATABASE_URL for PostgreSQL
```

5. **Initialize the database**
```bash
python app.py
```

The database will be created automatically on first run. The application will be available at `http://localhost:5000`

---

## ⚙️ Configuration

### Development Setup

For local development, the app uses SQLite:

```env
DATABASE_ENV=development
```

### Production Setup

For production deployment with PostgreSQL (Neon):

```env
DATABASE_ENV=production
DATABASE_URL=postgresql://user:password@host:5432/database
```

### API Rate Limiting

Default limits (configurable in `app.py`):
- General: 200 requests per day, 50 per hour
- Farm Plan Generation: 3 per day per user
- Plant Diagnosis: 3 per day per user

---

## 🌐 Deployment

### Deploying to Replit

1. Import the repository to Replit
2. Add your `GOOGLE_API_KEY` to Secrets
3. The app will auto-start on port 5000

### Deploying to Oracle Cloud

**Complete deployment guide:**

#### 1. Provision Oracle Cloud Infrastructure

```bash
# Create a Compute Instance (Ubuntu 22.04)
# Minimum: 1 OCPU, 1GB RAM
# Open ports: 80, 443, 5000
```

#### 2. Install Dependencies

```bash
# SSH into your instance
ssh ubuntu@your-instance-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.11 python3.11-venv python3-pip nginx -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y
```

#### 3. Set Up Application

```bash
# Clone your repository
git clone https://github.com/yourusername/yieldwise-ai.git
cd yieldwise-ai

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

#### 4. Configure Environment

```bash
# Create .env file
nano .env

# Add your configuration:
GOOGLE_API_KEY=your_key_here
SECRET_KEY=your_secret_key
DATABASE_ENV=production
DATABASE_URL=postgresql://user:password@localhost:5432/yieldwise
```

#### 5. Set Up PostgreSQL Database

```bash
# Create database and user
sudo -u postgres psql
CREATE DATABASE yieldwise;
CREATE USER yieldwiseuser WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE yieldwise TO yieldwiseuser;
\q
```

#### 6. Configure Gunicorn Service

```bash
# Create systemd service
sudo nano /etc/systemd/system/yieldwise.service

# Add configuration:
[Unit]
Description=YieldWise AI Application
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/yieldwise-ai
Environment="PATH=/home/ubuntu/yieldwise-ai/venv/bin"
ExecStart=/home/ubuntu/yieldwise-ai/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:5000 app:app

[Install]
WantedBy=multi-user.target
```

```bash
# Start and enable service
sudo systemctl start yieldwise
sudo systemctl enable yieldwise
```

#### 7. Configure Nginx Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/yieldwise

# Add configuration:
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/yieldwise /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

#### 8. Set Up SSL (Optional but Recommended)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

### Deploying to Other Platforms

The application is also compatible with:
- **Heroku**: Use the provided `Procfile`
- **AWS EC2**: Similar to Oracle Cloud setup
- **DigitalOcean**: Use App Platform or Droplets
- **Render**: Direct deploy from GitHub

---

## 📚 API Documentation

### Farm Plan Generation

**POST** `/api/generate`

```json
{
  "location": "Lagos",
  "space": "100 square meters",
  "budget": 50000,
  "country": "Nigeria",
  "currency": "NGN"
}
```

### Plant Diagnosis

**POST** `/api/diagnose`

```
Content-Type: multipart/form-data

plant_image: [file]
crop_type: "tomato"
```

### Follow-up Questions

**POST** `/api/follow_up`

```json
{
  "plan_id": 123,
  "question": "What are the best organic pesticides?"
}
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Onyeka Nwokike**  
Agricultural & Bioresources Engineer | Software Developer

- Portfolio: [nwokike.github.io/portfolio](https://nwokike.github.io/portfolio)
- GitHub: [@Nwokike](https://github.com/Nwokike)
- Email: nwokikeonyeka@gmail.com

---

## 🙏 Acknowledgments

- Google Gemini AI for powering the intelligent features
- Flask community for the excellent web framework
- All contributors and testers

---

<div align="center">

**Built with ❤️ for farmers worldwide**

[⬆ Back to Top](#-yieldwise-ai)

</div>
