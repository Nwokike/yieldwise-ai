# YieldWise AI - Deployment Guide

This guide covers deploying YieldWise AI to various cloud platforms, with detailed instructions for Oracle Cloud Infrastructure.

## Table of Contents

- [Oracle Cloud Deployment](#oracle-cloud-deployment)
- [PostgreSQL/Neon Setup](#postgresqlneon-setup)
- [Environment Configuration](#environment-configuration)
- [Production Checklist](#production-checklist)

---

## Oracle Cloud Deployment

### Prerequisites

- Oracle Cloud account with active subscription
- Domain name (optional but recommended)
- SSH key pair for server access

### Step 1: Create Compute Instance

1. **Navigate to Oracle Cloud Console**
   - Go to Compute → Instances
   - Click "Create Instance"

2. **Configure Instance**
   - **Name**: `yieldwise-ai-server`
   - **Image**: Ubuntu 22.04 (or latest LTS)
   - **Shape**: 
     - Development: VM.Standard.E2.1.Micro (1 OCPU, 1GB RAM) - Free tier
     - Production: VM.Standard.E4.Flex (2 OCPU, 8GB RAM) - Recommended
   - **Network**: Create or select existing VCN
   - **SSH Keys**: Upload your public key

3. **Configure Security**
   - In the VCN, go to Security Lists
   - Add Ingress Rules:
     ```
     Port 22  (SSH)
     Port 80  (HTTP)
     Port 443 (HTTPS)
     Port 5000 (Application - for testing)
     ```

### Step 2: Connect to Instance

```bash
ssh ubuntu@<your-instance-public-ip>
```

### Step 3: Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# Install other dependencies
sudo apt install nginx postgresql postgresql-contrib git build-essential -y

# Install pip for Python 3.11
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11
```

### Step 4: Set Up PostgreSQL

```bash
# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE yieldwise_production;
CREATE USER yieldwise WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE yieldwise_production TO yieldwise;
\q
EOF

# Note your DATABASE_URL will be:
# postgresql://yieldwise:your_secure_password_here@localhost:5432/yieldwise_production
```

### Step 5: Deploy Application

```bash
# Create application directory
cd /opt
sudo mkdir yieldwise-ai
sudo chown ubuntu:ubuntu yieldwise-ai
cd yieldwise-ai

# Clone repository
git clone https://github.com/yourusername/yieldwise-ai.git .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 6: Configure Environment

```bash
# Create .env file
nano .env
```

Add the following configuration:

```env
# Production Environment
GOOGLE_API_KEY=your_gemini_api_key_from_google
SECRET_KEY=your_very_secure_random_secret_key

# Database (PostgreSQL)
DATABASE_ENV=production
DATABASE_URL=postgresql://yieldwise:your_secure_password_here@localhost:5432/yieldwise_production
```

**Important**: Generate a secure SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 7: Initialize Database

```bash
# Run the application once to create tables
python app.py
# Press Ctrl+C after tables are created
```

### Step 8: Set Up Gunicorn Service

```bash
# Create systemd service file
sudo nano /etc/systemd/system/yieldwise.service
```

Add this configuration:

```ini
[Unit]
Description=YieldWise AI Application
After=network.target postgresql.service

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/yieldwise-ai
Environment="PATH=/opt/yieldwise-ai/venv/bin"
Environment="GOOGLE_API_KEY=your_key"
Environment="SECRET_KEY=your_secret"
Environment="DATABASE_ENV=production"
Environment="DATABASE_URL=postgresql://yieldwise:password@localhost:5432/yieldwise_production"

ExecStart=/opt/yieldwise-ai/venv/bin/gunicorn \
    --workers 4 \
    --bind 0.0.0.0:5000 \
    --timeout 120 \
    --access-logfile /var/log/yieldwise/access.log \
    --error-logfile /var/log/yieldwise/error.log \
    app:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Create log directory
sudo mkdir -p /var/log/yieldwise
sudo chown ubuntu:ubuntu /var/log/yieldwise

# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl start yieldwise
sudo systemctl enable yieldwise

# Check status
sudo systemctl status yieldwise
```

### Step 9: Configure Nginx Reverse Proxy

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/yieldwise
```

Add this configuration:

```nginx
upstream yieldwise {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # File upload size limit
    client_max_body_size 16M;

    location / {
        proxy_pass http://yieldwise;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # Static files (optional optimization)
    location /static {
        alias /opt/yieldwise-ai/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Enable site and restart Nginx
sudo ln -s /etc/nginx/sites-available/yieldwise /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

### Step 10: Set Up SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Certbot will automatically configure Nginx for HTTPS
# Test auto-renewal
sudo certbot renew --dry-run
```

---

## PostgreSQL/Neon Setup

### Using Neon (Serverless PostgreSQL)

Neon is a serverless PostgreSQL provider that's perfect for production deployments.

1. **Create Neon Account**
   - Go to [neon.tech](https://neon.tech)
   - Sign up for free account

2. **Create Database**
   - Click "Create Project"
   - Choose region closest to your users
   - Note the connection string

3. **Configure Application**

```env
DATABASE_ENV=production
DATABASE_URL=postgresql://username:password@ep-xxx.region.neon.tech/neondb?sslmode=require
```

4. **Initialize Database**

```bash
# Run app once to create tables
python app.py
```

### Using Oracle Autonomous Database

1. **Create Autonomous Database**
   - Go to Oracle Cloud → Autonomous Database
   - Create ATP (Transaction Processing) instance

2. **Download Wallet**
   - Download connection wallet
   - Extract to `/opt/oracle_wallet`

3. **Configure Connection**

```env
DATABASE_ENV=production
DATABASE_URL=oracle+cx_oracle://username:password@tnsname
```

---

## Environment Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Gemini API key | `AIzaSy...` |
| `SECRET_KEY` | Flask secret key | Random 64-char hex |
| `DATABASE_ENV` | Environment | `production` |
| `DATABASE_URL` | Database connection | `postgresql://...` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_CONTENT_LENGTH` | Max upload size | 16MB |
| `FLASK_ENV` | Flask environment | `production` |

---

## Production Checklist

### Security

- [ ] Set strong `SECRET_KEY`
- [ ] Configure SSL/HTTPS
- [ ] Set up firewall rules
- [ ] Enable database SSL connections
- [ ] Configure rate limiting
- [ ] Set up CORS policies (if needed)
- [ ] Implement proper logging

### Performance

- [ ] Configure Gunicorn workers (4-12 recommended)
- [ ] Set up Nginx caching for static files
- [ ] Enable Gzip compression
- [ ] Configure database connection pooling
- [ ] Set up CDN for static assets (optional)

### Monitoring

- [ ] Set up application logging
- [ ] Configure error tracking (Sentry recommended)
- [ ] Set up uptime monitoring
- [ ] Configure database backups
- [ ] Set up performance monitoring

### Maintenance

```bash
# View application logs
sudo journalctl -u yieldwise -f

# Restart application
sudo systemctl restart yieldwise

# Update application
cd /opt/yieldwise-ai
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart yieldwise

# Database backup
pg_dump yieldwise_production > backup_$(date +%Y%m%d).sql
```

---

## Troubleshooting

### Application Won't Start

```bash
# Check logs
sudo journalctl -u yieldwise -n 50

# Check if port 5000 is in use
sudo netstat -tulpn | grep 5000

# Verify environment variables
cat .env
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -U yieldwise -d yieldwise_production -h localhost

# Check if PostgreSQL is running
sudo systemctl status postgresql
```

### Nginx Issues

```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log
```

### SSL Certificate Issues

```bash
# Renew certificate manually
sudo certbot renew

# Check certificate expiry
sudo certbot certificates
```

---

## Scaling & Optimization

### Horizontal Scaling

- Use Oracle Load Balancer to distribute traffic
- Deploy multiple instances in different availability domains
- Configure database read replicas

### Caching

```python
# Add Flask-Caching
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'redis'})
```

### Background Jobs

For long-running tasks, consider:
- Celery with Redis
- Oracle Queue Service
- Background workers for PDF generation

---

## Support

For deployment issues:
- Check application logs: `sudo journalctl -u yieldwise -f`
- Review Nginx logs: `sudo tail -f /var/log/nginx/error.log`
- Database logs: `sudo tail -f /var/log/postgresql/postgresql-*.log`

For production support, contact: nwokikeonyeka@gmail.com
