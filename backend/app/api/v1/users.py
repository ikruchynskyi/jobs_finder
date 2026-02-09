"""
Users API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import os

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


from app.services.parser import extract_text_from_file
from app.models.models import Resume

@router.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload resume file and extract text"""
    # Validate file type
    allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    
    if file.content_type not in allowed_types and not file.filename.lower().endswith(('.pdf', '.docx')):
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
    
    # Extract text
    # We need to read the file again or save it temporarily to extract text if upload_file_to_storage consumes it
    # For now assuming we can re-read or using a temp path pattern. 
    # Since upload_file_to_storage likely consumes the stream, we might need to handle this carefully.
    # Ideally upload_file_to_storage should return the local path or we save it first.
    # Simpler approach for now: rely on the file path if local, or re-download. 
    # actually parser needs a file path. 
    
    # HACK: For local dev, constructing path from storage logic
    # In production with S3, we'd need to download it back.
    # Assuming local storage for now based on project structure.
    upload_dir = f"/app/storage/users/{current_user.id}/resume"
    local_path = os.path.join(upload_dir, file.filename)
    
    text = await extract_text_from_file(local_path, file.content_type)
    
    # Create Resume record
    resume = Resume(
        user_id=current_user.id,
        file_url=file_url,
        file_name=file.filename,
        extracted_text=text
    )
    db.add(resume)
    
    # Update profile default resume if none
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if profile and not profile.resume_url:
        profile.resume_url = file_url
        
    db.commit()
    
    return {
        "message": "Resume uploaded and processed successfully",
        "file_url": file_url,
        "resume_id": resume.id
    }

@router.get("/resumes")
async def get_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all uploaded resumes"""
    resumes = db.query(Resume).filter(Resume.user_id == current_user.id).all()
    return resumes

@router.post("/gemini-key")
async def set_gemini_key(
    key_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Set Gemini API Key"""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
    
    profile.gemini_api_key = key_data.get('api_key')
    db.commit()
    return {"message": "API Key saved successfully"}

@router.delete("/me")
async def delete_user_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete user account"""
    db.delete(current_user)
    db.commit()
    return {"message": "Account deleted successfully"}


from app.services.applicator import JobApplicator
from app.schemas.schemas import LinkedInLoginRequest

@router.post("/connect-linkedin")
async def connect_linkedin(
    login_data: LinkedInLoginRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Connect to LinkedIn by logging in and retrieving the session cookie.
    """
    applicator = JobApplicator()
    try:
        cookie = applicator.login_linkedin(login_data.email, login_data.password)
        
        # Save cookie to profile
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()
        
        if not profile:
            # Create profile if not exists
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)
        
        profile.linkedin_cookies = cookie
        profile.linkedin_url = f"https://www.linkedin.com/in/{current_user.username}" # heuristic
        db.commit()
        
        return {"message": "Successfully connected to LinkedIn", "cookie": cookie}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
