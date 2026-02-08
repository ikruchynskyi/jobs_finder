# Complete Deployment Guide
## AutoApply - Job Application Automation Platform

This guide covers deploying both the backend and frontend of the AutoApply platform.

---

## Table of Contents

1. [Quick Start with Docker](#quick-start-with-docker)
2. [Google OAuth Setup](#google-oauth-setup)
3. [Local Development](#local-development)
4. [Production Deployment](#production-deployment)
5. [Environment Variables](#environment-variables)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start with Docker

The fastest way to get the entire stack running.

### Step 1: Prerequisites

```bash
# Install Docker and Docker Compose
# macOS: https://docs.docker.com/desktop/mac/install/
# Windows: https://docs.docker.com/desktop/windows/install/
# Linux: https://docs.docker.com/engine/install/

# Verify installation
docker --version
docker-compose --version
```

### Step 2: Clone and Configure

```bash
# Navigate to project directory
cd job-automation-platform

# Copy environment file
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your favorite editor
```

### Step 3: Set Up Google OAuth (Required for Frontend)

See [Google OAuth Setup](#google-oauth-setup) section below.

Add to `.env`:
```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

### Step 4: Start Everything

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 5: Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001
- **Selenium Grid**: http://localhost:4444

### Step 6: Create Your First Account

1. Go to http://localhost:3000
2. Click "Continue with Google" or "Get Started Free"
3. Complete registration
4. Upload your resume
5. Start applying to jobs!

---

## Google OAuth Setup

Required for "Sign in with Google" functionality.

### Create Google OAuth Credentials

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Create a Project**
   - Click "Select a project" → "New Project"
   - Name: "AutoApply" (or your preferred name)
   - Click "Create"

3. **Enable Google+ API**
   - Go to "APIs & Services" → "Library"
   - Search for "Google+ API"
   - Click "Enable"

4. **Configure OAuth Consent Screen**
   - Go to "APIs & Services" → "OAuth consent screen"
   - User Type: "External" (for testing) or "Internal" (for organization)
   - Fill in:
     - App name: "AutoApply"
     - User support email: your email
     - Developer contact: your email
   - Click "Save and Continue"
   - Scopes: Add email, profile (default scopes)
   - Test users: Add your email
   - Click "Save and Continue"

5. **Create OAuth Client ID**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Web application"
   - Name: "AutoApply Web Client"
   - Authorized redirect URIs:
     ```
     http://localhost:3000/api/auth/callback/google
     https://yourdomain.com/api/auth/callback/google
     ```
   - Click "Create"

6. **Copy Credentials**
   - Copy Client ID and Client Secret
   - Add to `.env` file:
   ```env
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

---

## Local Development

For development without Docker.

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
createdb jobautomation

# Run migrations (if using Alembic)
alembic upgrade head

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.local.example .env.local

# Edit .env.local with your settings
nano .env.local

# Start development server
npm run dev
```

### Required Services

You'll still need PostgreSQL, Redis, and Chrome for Selenium:

```bash
# PostgreSQL
brew install postgresql  # macOS
sudo apt install postgresql  # Ubuntu

# Redis
brew install redis  # macOS
sudo apt install redis-server  # Ubuntu

# Start services
brew services start postgresql
brew services start redis
```

---

## Production Deployment

### Option 1: AWS ECS/Fargate (Recommended)

#### Backend Deployment

1. **Build and Push Docker Image**
```bash
# Build image
docker build -t autoapply-backend ./backend

# Tag for ECR
docker tag autoapply-backend:latest \
  123456789.dkr.ecr.us-east-1.amazonaws.com/autoapply-backend:latest

# Push to ECR
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/autoapply-backend:latest
```

2. **Create ECS Task Definition**
```json
{
  "family": "autoapply-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/autoapply-backend:latest",
      "portMappings": [{"containerPort": 8000}],
      "environment": [
        {"name": "DATABASE_URL", "value": "postgresql://..."},
        {"name": "REDIS_URL", "value": "redis://..."}
      ]
    }
  ]
}
```

3. **Create ECS Service**
- Load balancer: Application Load Balancer
- Target group: Port 8000
- Health check: `/health`
- Auto-scaling: Min 2, Max 10 tasks

#### Frontend Deployment

**Using Vercel (Easiest)**

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel --prod

# Set environment variables in Vercel dashboard
```

**Using AWS Amplify**

1. Connect GitHub repository
2. Build settings:
   ```yaml
   version: 1
   frontend:
     phases:
       preBuild:
         commands:
           - cd frontend
           - npm install
       build:
         commands:
           - npm run build
     artifacts:
       baseDirectory: frontend/.next
       files:
         - '**/*'
   ```
3. Add environment variables

### Option 2: DigitalOcean App Platform

1. **Create App**
   - Connect GitHub repository
   - Select branch

2. **Configure Services**
   
   **Backend:**
   - Type: Web Service
   - Source: `/backend`
   - Build Command: `pip install -r requirements.txt`
   - Run Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
   
   **Frontend:**
   - Type: Static Site
   - Source: `/frontend`
   - Build Command: `npm run build`
   - Output Directory: `.next`

3. **Add Databases**
   - PostgreSQL cluster
   - Redis cluster

4. **Configure Environment Variables**

### Option 3: Self-Hosted VPS

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Clone repository
git clone https://github.com/yourusername/autoapply.git
cd autoapply

# Configure environment
cp .env.example .env
nano .env

# Start with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Set up Nginx reverse proxy
# Set up SSL with Let's Encrypt
```

---

## Environment Variables

### Backend (.env)

```env
# API Settings
API_V1_PREFIX=/api/v1
PROJECT_NAME=AutoApply

# Security
SECRET_KEY=generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis
REDIS_URL=redis://host:6379/0
CELERY_BROKER_URL=redis://host:6379/0

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# S3 Storage
S3_BUCKET=autoapply-files
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret

# Selenium
SELENIUM_HEADLESS=true
SELENIUM_TIMEOUT=30
```

### Frontend (.env.local)

```env
# Backend API
NEXT_PUBLIC_API_URL=https://api.yourdomain.com

# NextAuth
NEXTAUTH_URL=https://yourdomain.com
NEXTAUTH_SECRET=generate-with-openssl-rand-hex-32

# Google OAuth
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret
```

---

## SSL/HTTPS Setup

### Using Certbot (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal (runs twice daily)
sudo systemctl enable certbot.timer
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Monitoring & Logging

### Application Monitoring

```bash
# Backend logs
docker-compose logs -f backend

# Frontend logs
docker-compose logs -f frontend

# All services
docker-compose logs -f
```

### Production Monitoring

**Sentry (Error Tracking)**
```bash
# Backend
pip install sentry-sdk

# Frontend
npm install @sentry/nextjs
```

**Prometheus + Grafana**
- Metrics collection
- Dashboard visualization
- Alerting

---

## Scaling Considerations

### Horizontal Scaling

**Backend:**
- Run multiple API instances behind load balancer
- Increase Celery workers based on load
- Use connection pooling for database

**Frontend:**
- Deploy to CDN (Vercel, Netlify, CloudFlare)
- Enable caching
- Use Next.js ISR for static pages

### Database Scaling

- Read replicas for read-heavy workloads
- Connection pooling (PgBouncer)
- Query optimization
- Partition large tables

### Caching Strategy

- Redis for session storage
- Redis for API response caching
- CDN for static assets
- Browser caching headers

---

## Backup Strategy

### Database Backups

```bash
# Automated daily backups
0 2 * * * pg_dump -U user dbname > backup_$(date +\%Y\%m\%d).sql

# Backup to S3
aws s3 cp backup.sql s3://your-bucket/backups/
```

### File Storage Backups

```bash
# S3 versioning enabled
# Cross-region replication for critical files
```

---

## Troubleshooting

### Common Issues

**Google OAuth not working:**
- Verify redirect URIs match exactly
- Check Client ID/Secret are correct
- Ensure in production, NEXTAUTH_URL uses HTTPS

**Database connection errors:**
- Check DATABASE_URL format
- Verify database is running
- Check firewall rules

**Selenium timeout errors:**
- Increase SELENIUM_TIMEOUT
- Add more Chrome nodes
- Check memory limits

**Build failures:**
- Clear caches: `docker-compose build --no-cache`
- Check logs: `docker-compose logs`
- Verify environment variables

### Getting Help

1. Check logs: `docker-compose logs -f [service]`
2. Verify environment variables
3. Test API endpoints: `curl http://localhost:8000/health`
4. Check documentation

---

## Security Checklist

✅ Change all default passwords  
✅ Use environment variables for secrets  
✅ Enable HTTPS in production  
✅ Set up firewall rules  
✅ Regular security updates  
✅ Monitor for unusual activity  
✅ Backup data regularly  
✅ Use strong JWT secrets  
✅ Implement rate limiting  
✅ Validate all user input  

---

## Production URLs

After deployment, update these in your environment:

- Frontend: https://yourdomain.com
- Backend API: https://api.yourdomain.com
- Admin Panel: https://admin.yourdomain.com (if implemented)

---

**Congratulations! Your AutoApply platform is now deployed! 🎉**

For support or questions, check the project documentation or create an issue on GitHub.
