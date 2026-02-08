"""
Jobs API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import Job, User, SavedJob, JobSource
from app.schemas.schemas import (
    JobResponse, 
    JobSearch, 
    CrawlerJobCreate, 
    CrawlerJobResponse
)
from app.services.crawler import start_crawler_job

router = APIRouter()


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    source: Optional[JobSource] = None,
    remote_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all available jobs with filtering"""
    query = db.query(Job).filter(Job.is_active == True)
    
    if source:
        query = query.filter(Job.source == source)
    
    if remote_only:
        query = query.filter(Job.remote == True)
    
    jobs = query.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific job by ID"""
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    return job


@router.post("/search")
async def search_jobs(
    search: JobSearch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Search for jobs in the database"""
    query = db.query(Job).filter(Job.is_active == True)
    
    # Search in title, company, description
    if search.query:
        search_filter = f"%{search.query}%"
        query = query.filter(
            (Job.title.ilike(search_filter)) |
            (Job.company.ilike(search_filter)) |
            (Job.description.ilike(search_filter))
        )
    
    if search.location:
        query = query.filter(Job.location.ilike(f"%{search.location}%"))
    
    if search.source:
        query = query.filter(Job.source == search.source)
    
    if search.remote_only:
        query = query.filter(Job.remote == True)
    
    if search.min_salary:
        query = query.filter(Job.salary_min >= search.min_salary)
    
    jobs = query.order_by(Job.created_at.desc()).limit(50).all()
    return {"results": jobs, "count": len(jobs)}


@router.post("/crawl", response_model=CrawlerJobResponse)
async def crawl_jobs(
    crawler_config: CrawlerJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Start a job crawling task"""
    # Create crawler job record
    from app.models.models import CrawlerJob
    
    crawler_job = CrawlerJob(
        user_id=current_user.id,
        search_query=crawler_config.search_query,
        location=crawler_config.location,
        source=crawler_config.source,
        status="queued"
    )
    
    db.add(crawler_job)
    db.commit()
    db.refresh(crawler_job)
    
    # Queue background task
    background_tasks.add_task(
        start_crawler_job,
        crawler_job.id,
        crawler_config.search_query,
        crawler_config.location,
        crawler_config.source
    )
    
    return crawler_job


@router.post("/{job_id}/save")
async def save_job(
    job_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Save a job for later"""
    # Check if job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if already saved
    existing = db.query(SavedJob).filter(
        SavedJob.user_id == current_user.id,
        SavedJob.job_id == job_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Job already saved"
        )
    
    # Save job
    saved_job = SavedJob(
        user_id=current_user.id,
        job_id=job_id,
        notes=notes
    )
    
    db.add(saved_job)
    db.commit()
    
    return {"message": "Job saved successfully"}


@router.get("/saved/list")
async def list_saved_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all saved jobs for current user"""
    saved_jobs = db.query(SavedJob).filter(
        SavedJob.user_id == current_user.id
    ).all()
    
    return {"saved_jobs": saved_jobs}
