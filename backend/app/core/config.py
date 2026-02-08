"""
Core Configuration
"""
from pydantic_settings import BaseSettings
from typing import List
import secrets


class Settings(BaseSettings):
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Job Automation Platform"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/jobautomation"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    
    # File Storage
    S3_BUCKET: str = "job-automation-files"
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Selenium Settings
    SELENIUM_HEADLESS: bool = True
    SELENIUM_TIMEOUT: int = 30
    SELENIUM_URL: str = "http://selenium-hub:4444/wd/hub"
    MAX_CONCURRENT_APPLICATIONS: int = 5
    
    # Job Crawler Settings
    CRAWLER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    CRAWLER_RATE_LIMIT: int = 2  # seconds between requests
    
    # Supported Job Platforms
    SUPPORTED_PLATFORMS: List[str] = [
        "linkedin",
        "indeed",
        "glassdoor",
        "ziprecruiter",
        "monster"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
