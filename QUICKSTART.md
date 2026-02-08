# Quick Start Guide
## Job Application Automation Platform

---

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose installed
- Python 3.11+ (for local development)
- PostgreSQL 14+ (if not using Docker)
- Redis (if not using Docker)

---

## 📦 Installation

### Option 1: Docker (Recommended)

1. **Clone and setup:**
```bash
cd job-automation-platform
cp .env.example .env
```

2. **Edit .env file:**
Update the following values:
```env
SECRET_KEY=your-generated-secret-key
DATABASE_URL=postgresql://jobautomation:securepassword123@postgres:5432/jobautomation
```

3. **Start all services:**
```bash
docker-compose up -d
```

4. **Check services are running:**
```bash
docker-compose ps
```

You should see:
- ✅ PostgreSQL (port 5432)
- ✅ Redis (port 6379)
- ✅ FastAPI backend (port 8000)
- ✅ Celery worker
- ✅ Selenium Hub (port 4444)

5. **Access the API:**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Selenium Grid: http://localhost:4444

---

### Option 2: Local Development

1. **Install dependencies:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Setup database:**
```bash
# Create PostgreSQL database
createdb jobautomation

# Run migrations (if using Alembic)
alembic upgrade head
```

3. **Start Redis:**
```bash
redis-server
```

4. **Start the API:**
```bash
uvicorn app.main:app --reload
```

5. **Start Celery worker (in new terminal):**
```bash
celery -A app.workers.celery_worker worker --loglevel=info
```

---

## 🧪 Testing the API

### 1. Register a new user:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "securepass123",
    "full_name": "Test User"
  }'
```

### 2. Login:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=securepass123"
```

Save the `access_token` from the response.

### 3. Create user profile:
```bash
curl -X POST "http://localhost:8000/api/v1/users/profile" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "skills": ["Python", "JavaScript", "AWS"],
    "experience_years": 5,
    "location": "San Francisco, CA",
    "phone": "+1234567890"
  }'
```

### 4. Start a job crawler:
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/crawl" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "search_query": "Software Engineer",
    "location": "San Francisco",
    "source": "linkedin"
  }'
```

### 5. List available jobs:
```bash
curl -X GET "http://localhost:8000/api/v1/jobs/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 6. Apply to a job:
```bash
curl -X POST "http://localhost:8000/api/v1/applications/apply" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 1
  }'
```

---

## 📊 Monitoring

### View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery-worker
```

### Check Celery tasks:
```bash
docker exec -it job_automation_worker celery -A app.workers.celery_worker inspect active
```

### Database access:
```bash
docker exec -it job_automation_db psql -U jobautomation
```

---

## 🔧 Development

### Run tests:
```bash
cd backend
pytest
```

### Format code:
```bash
black app/
flake8 app/
```

### Create database migration:
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

---

## 🐛 Troubleshooting

### Issue: "Connection refused" to database
**Solution:**
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Check if it's running
docker-compose ps postgres
```

### Issue: Selenium browser not starting
**Solution:**
```bash
# Check Chrome installation
docker exec -it job_automation_worker google-chrome --version

# Check Selenium Grid
curl http://localhost:4444/status
```

### Issue: Celery worker not processing tasks
**Solution:**
```bash
# Restart worker
docker-compose restart celery-worker

# Check worker logs
docker-compose logs celery-worker
```

### Issue: "Module not found" errors
**Solution:**
```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 🔐 Security Notes

1. **Change default passwords** in .env file
2. **Use environment variables** for sensitive data
3. **Enable HTTPS** in production
4. **Implement rate limiting** for API endpoints
5. **Regular security updates** for dependencies

---

## 📈 Scaling

### Scale workers:
```bash
docker-compose up -d --scale celery-worker=5
```

### Monitor performance:
- CPU usage: `docker stats`
- Database connections: Check PostgreSQL logs
- Redis memory: `docker exec job_automation_redis redis-cli info memory`

---

## 🚢 Production Deployment

### Deploy to AWS ECS:
1. Push Docker images to ECR
2. Create ECS cluster
3. Define task definitions
4. Configure load balancer
5. Set up auto-scaling

### Environment Variables:
```env
DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/db
REDIS_URL=redis://elasticache-endpoint:6379
S3_BUCKET=your-production-bucket
SELENIUM_HEADLESS=true
```

---

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 🤝 Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review API docs: http://localhost:8000/docs
3. Check TECHNOLOGY_RECOMMENDATIONS.md for architecture details

---

## 📝 Next Steps

1. ✅ Setup complete
2. 🔨 Customize job crawler for specific platforms
3. 🎨 Build frontend (React/Next.js)
4. 🔔 Add notification system
5. 📊 Implement analytics dashboard
6. 🔐 Add OAuth providers (Google, LinkedIn)
7. 💳 Integrate payment system (if needed)
8. 🌍 Deploy to production

---

**Ready to automate job applications! 🚀**
