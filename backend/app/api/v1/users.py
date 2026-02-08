"""
Users API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.models import User, UserProfile
from app.schemas.schemas import (
    UserResponse, 
    UserProfileCreate, 
    UserProfileUpdate,
    UserProfileResponse
)
from app.services.storage import upload_file_to_storage

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user profile"""
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile


@router.post("/profile", response_model=UserProfileResponse, status_code=201)
async def create_user_profile(
    profile_data: UserProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create user profile"""
    # Check if profile already exists
    existing = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Profile already exists. Use PUT to update."
        )
    
    profile = UserProfile(
        user_id=current_user.id,
        **profile_data.dict()
    )
    
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return profile


@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update user profile"""
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Update only provided fields
    update_data = profile_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    
    return profile


@router.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload resume file"""
    # Validate file type
    allowed_types = ["application/pdf", "application/msword", 
                     "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and Word documents are allowed"
        )
    
    # Upload to storage
    file_url = await upload_file_to_storage(
        file=file,
        user_id=current_user.id,
        file_type="resume"
    )
    
    # Update profile with resume URL
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()
    
    if profile:
        profile.resume_url = file_url
        db.commit()
    
    return {
        "message": "Resume uploaded successfully",
        "file_url": file_url
    }


@router.delete("/me")
async def delete_user_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete user account"""
    # This will cascade delete all related data
    db.delete(current_user)
    db.commit()
    
    return {"message": "Account deleted successfully"}
