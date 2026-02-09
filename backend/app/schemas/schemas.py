"""
Pydantic Schemas for Request/Response Validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.models import ApplicationStatus, JobSource


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class OAuthRegisterLogin(BaseModel):
    """Register or login via OAuth (Google). No password needed."""
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    provider: str = "google"


class LinkedInLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# Job Schemas
class JobBase(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    job_type: Optional[str] = None
    remote: bool = False
    source: JobSource
    source_url: str


class JobCreate(JobBase):
    external_id: str
    posted_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class JobResponse(JobBase):
    id: int
    external_id: Optional[str] = None
    posted_date: Optional[datetime]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class JobSearch(BaseModel):
    query: str
    location: Optional[str] = None
    source: Optional[JobSource] = None
    remote_only: bool = False
    min_salary: Optional[int] = None


# Application Schemas
class ApplicationBase(BaseModel):
    job_id: int


class ApplicationCreate(ApplicationBase):
    resume_url: Optional[str] = None
    cover_letter: Optional[str] = None


class BatchApplicationCreate(BaseModel):
    """Apply to multiple jobs at once."""
    job_ids: List[int] = Field(..., min_length=1, max_length=50)
    resume_url: Optional[str] = None
    cover_letter: Optional[str] = None


class ApplicationResponse(ApplicationBase):
    id: int
    user_id: int
    status: ApplicationStatus
    applied_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    job: JobResponse
    
    class Config:
        from_attributes = True


# User Profile Schemas
class UserProfileBase(BaseModel):
    resume_url: Optional[str] = None
    cover_letter_template: Optional[str] = None
    skills: Optional[List[str]] = None
    experience_years: Optional[int] = None
    linkedin_url: Optional[str] = None
    linkedin_cookies: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    job_preferences: Optional[Dict[str, Any]] = None


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfileResponse(UserProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Crawler Schemas
class CrawlerJobCreate(BaseModel):
    search_query: str
    location: Optional[str] = None
    source: JobSource


# AI Usage Schemas
class AIUsageByService(BaseModel):
    service_type: str
    request_count: int
    total_tokens: int
    total_input_tokens: int
    total_output_tokens: int


class AIUsageStatsResponse(BaseModel):
    total_requests: int
    total_tokens: int
    total_input_tokens: int
    total_output_tokens: int
    requests_today: int
    tokens_today: int
    by_service: List[AIUsageByService]


class CrawlerJobResponse(BaseModel):
    id: int
    search_query: str
    location: Optional[str]
    source: JobSource
    status: str
    jobs_found: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True
