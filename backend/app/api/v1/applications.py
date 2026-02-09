"""
Job Applications API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import JobApplication, Job, User, ApplicationStatus
from app.schemas.schemas import ApplicationCreate, ApplicationResponse
from app.services.applicator import apply_to_job_task

router = APIRouter()


@router.post("/apply", response_model=ApplicationResponse, status_code=201)
async def apply_to_job(
    application_data: ApplicationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Apply to a job (creates application and queues automation task)"""
    # Check if job exists
    job = db.query(Job).filter(Job.id == application_data.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if already applied
    existing = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id,
        JobApplication.job_id == application_data.job_id
    ).first()
    
    if existing:
        if existing.status == ApplicationStatus.FAILED:
            # Reset and retry
            existing.status = ApplicationStatus.PENDING
            existing.error_message = None
            existing.automation_log = None
            existing.applied_at = None
            existing.created_at = datetime.utcnow()
            
            db.commit()
            db.refresh(existing)
            
            # Queue background task
            background_tasks.add_task(
                apply_to_job_task,
                existing.id,
                current_user.id,
                job.id
            )
            return existing
            
        raise HTTPException(
            status_code=400,
            detail="Already applied to this job"
        )
    
    # Create application record
    application = JobApplication(
        user_id=current_user.id,
        job_id=application_data.job_id,
        status=ApplicationStatus.PENDING,
        resume_used=application_data.resume_url,
        cover_letter_used=application_data.cover_letter
    )
    
    db.add(application)
    db.commit()
    db.refresh(application)
    
    # Queue background task for automated application
    background_tasks.add_task(
        apply_to_job_task,
        application.id,
        current_user.id,
        job.id
    )
    
    return application


@router.get("/", response_model=List[ApplicationResponse])
async def list_applications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: ApplicationStatus = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all applications for current user"""
    query = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id
    )
    
    if status:
        query = query.filter(JobApplication.status == status)
    
    applications = query.order_by(
        JobApplication.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return applications


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific application"""
    application = db.query(JobApplication).filter(
        JobApplication.id == application_id,
        JobApplication.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return application


@router.patch("/{application_id}/status")
async def update_application_status(
    application_id: int,
    status: ApplicationStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update application status manually"""
    application = db.query(JobApplication).filter(
        JobApplication.id == application_id,
        JobApplication.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    application.status = status
    db.commit()
    
    return {"message": "Status updated successfully"}


@router.delete("/{application_id}")
async def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an application"""
    application = db.query(JobApplication).filter(
        JobApplication.id == application_id,
        JobApplication.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Only allow deletion if not yet applied
    if application.status in [ApplicationStatus.APPLIED, ApplicationStatus.INTERVIEW, ApplicationStatus.ACCEPTED]:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete application that has been submitted"
        )
    
    db.delete(application)
    db.commit()
    
    return {"message": "Application deleted successfully"}


@router.get("/stats/summary")
async def get_application_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get application statistics for current user"""
    total = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id
    ).count()
    
    pending = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id,
        JobApplication.status == ApplicationStatus.PENDING
    ).count()
    
    applied = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id,
        JobApplication.status == ApplicationStatus.APPLIED
    ).count()
    
    interviews = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id,
        JobApplication.status == ApplicationStatus.INTERVIEW
    ).count()
    
    failed = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id,
        JobApplication.status == ApplicationStatus.FAILED
    ).count()
    
    return {
        "total": total,
        "pending": pending,
        "applied": applied,
        "interviews": interviews,
        "failed": failed,
        "success_rate": (applied / total * 100) if total > 0 else 0
    }
