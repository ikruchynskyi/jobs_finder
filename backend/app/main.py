"""
FastAPI Main Application
Job Application Automation Platform
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging
import os

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import auth, jobs, applications, users
from app.core.security import get_current_active_user
from app.models.models import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STORAGE_DIR = os.environ.get("STORAGE_DIR", "/app/storage")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting up...")
    Base.metadata.create_all(bind=engine)
    os.makedirs(os.path.join(STORAGE_DIR, "screenshots"), exist_ok=True)
    yield
    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title="Job Automation API",
    version="1.0.0",
    description="API for automated job application platform",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(applications.router, prefix="/api/v1/applications", tags=["applications"])


@app.get("/static/{file_path:path}")
async def serve_protected_file(
    file_path: str,
    current_user: User = Depends(get_current_active_user),
):
    """Serve storage files with authentication.
    Users can only access their own files or shared screenshots."""
    full_path = os.path.normpath(os.path.join(STORAGE_DIR, file_path))

    # Prevent directory traversal
    if not full_path.startswith(os.path.normpath(STORAGE_DIR)):
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Allow access to own files or screenshots (which may be shared with support)
    user_dir = f"users/{current_user.id}/"
    is_own_file = user_dir in file_path
    is_screenshot = file_path.startswith("screenshots/")

    if not is_own_file and not is_screenshot:
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(full_path)


@app.get("/")
async def root():
    return {
        "message": "Job Automation API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
