"""
Core Configuration
"""
from pydantic_settings import BaseSettings
from typing import List
import secrets
import os


# Generate a stable secret key: persist to .env so it survives restarts
def _get_or_create_secret_key() -> str:
    """Return SECRET_KEY from env, or generate one and persist it."""
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    # Generate and persist so JWT tokens survive restarts
    key = secrets.token_urlsafe(64)
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    try:
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                lines = f.readlines()
        # Append SECRET_KEY if not already present
        has_key = any(line.strip().startswith("SECRET_KEY=") for line in lines)
        if not has_key:
            with open(env_path, "a") as f:
                f.write(f"\nSECRET_KEY={key}\n")
    except OSError:
        pass  # In containers without write access, key lives in memory this run
    return key


class Settings(BaseSettings):
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Job Automation Platform"

    # Security
    SECRET_KEY: str = _get_or_create_secret_key()
    ENCRYPTION_KEY: str = ""  # Fernet key for encrypting sensitive fields
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
    LINKEDIN_LI_AT: str = ""  # LinkedIn Session Cookie

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
