"""
Database Models
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPLIED = "applied"
    FAILED = "failed"
    REJECTED = "rejected"
    INTERVIEW = "interview"
    ACCEPTED = "accepted"


class JobSource(str, enum.Enum):
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    GLASSDOOR = "glassdoor"
    ZIPRECRUITER = "ziprecruiter"
    MONSTER = "monster"
    CUSTOM = "custom"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profiles = relationship("UserProfile", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("JobApplication", back_populates="user", cascade="all, delete-orphan")
    saved_jobs = relationship("SavedJob", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resume_url = Column(String)
    cover_letter_template = Column(Text)
    skills = Column(JSON)  # ["Python", "JavaScript", "AWS"]
    experience_years = Column(Integer)
    linkedin_url = Column(String)
    github_url = Column(String)
    portfolio_url = Column(String)
    phone = Column(String)
    location = Column(String)
    job_preferences = Column(JSON)  # {remote: true, salary_min: 80000, etc}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="profiles")


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)  # Job ID from source platform
    title = Column(String, nullable=False, index=True)
    company = Column(String, nullable=False, index=True)
    location = Column(String)
    description = Column(Text)
    requirements = Column(Text)
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    job_type = Column(String)  # full-time, part-time, contract
    remote = Column(Boolean, default=False)
    source = Column(Enum(JobSource), nullable=False)
    source_url = Column(String, nullable=False)
    posted_date = Column(DateTime)
    expires_date = Column(DateTime)
    metadata = Column(JSON)  # Additional platform-specific data
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    applications = relationship("JobApplication", back_populates="job")
    saved_by = relationship("SavedJob", back_populates="job")


class JobApplication(Base):
    __tablename__ = "job_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.PENDING)
    resume_used = Column(String)
    cover_letter_used = Column(Text)
    applied_at = Column(DateTime)
    error_message = Column(Text)
    automation_log = Column(JSON)  # Log of automation steps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")


class SavedJob(Base):
    __tablename__ = "saved_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="saved_jobs")
    job = relationship("Job", back_populates="saved_by")


class CrawlerJob(Base):
    __tablename__ = "crawler_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    search_query = Column(String, nullable=False)
    location = Column(String)
    source = Column(Enum(JobSource), nullable=False)
    status = Column(String, default="queued")  # queued, running, completed, failed
    jobs_found = Column(Integer, default=0)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
