"""
File Storage Service
Handles file uploads to S3 or local storage
"""
import boto3
from botocore.exceptions import ClientError
import logging
import os
from pathlib import Path
from fastapi import UploadFile, HTTPException
import uuid

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Handle file storage operations"""
    
    def __init__(self):
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.S3_REGION
            )
            self.use_s3 = True
        else:
            self.use_s3 = False
            self.local_storage_path = Path("/home/claude/storage")
            self.local_storage_path.mkdir(exist_ok=True)
    
    async def upload_file(self, file: UploadFile, user_id: int, file_type: str) -> str:
        """
        Upload file to storage
        Returns: URL or path to the uploaded file
        """
        # Validate file size
        contents = await file.read()
        if len(contents) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed ({settings.MAX_FILE_SIZE} bytes)"
            )
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{user_id}/{file_type}/{uuid.uuid4()}{file_extension}"
        
        if self.use_s3:
            return await self._upload_to_s3(contents, unique_filename, file.content_type)
        else:
            return await self._upload_to_local(contents, unique_filename)
    
    async def _upload_to_s3(self, contents: bytes, filename: str, content_type: str) -> str:
        """Upload file to S3"""
        try:
            self.s3_client.put_object(
                Bucket=settings.S3_BUCKET,
                Key=filename,
                Body=contents,
                ContentType=content_type
            )
            
            # Generate URL
            url = f"https://{settings.S3_BUCKET}.s3.{settings.S3_REGION}.amazonaws.com/{filename}"
            logger.info(f"Uploaded file to S3: {url}")
            return url
            
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            raise HTTPException(status_code=500, detail="File upload failed")
    
    async def _upload_to_local(self, contents: bytes, filename: str) -> str:
        """Upload file to local storage"""
        try:
            file_path = self.local_storage_path / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, "wb") as f:
                f.write(contents)
            
            # Return relative path
            url = f"/storage/{filename}"
            logger.info(f"Uploaded file locally: {url}")
            return url
            
        except Exception as e:
            logger.error(f"Local storage error: {e}")
            raise HTTPException(status_code=500, detail="File upload failed")
    
    async def delete_file(self, file_url: str):
        """Delete file from storage"""
        if self.use_s3:
            await self._delete_from_s3(file_url)
        else:
            await self._delete_from_local(file_url)
    
    async def _delete_from_s3(self, file_url: str):
        """Delete file from S3"""
        try:
            # Extract key from URL
            key = file_url.split(f"{settings.S3_BUCKET}.s3.{settings.S3_REGION}.amazonaws.com/")[-1]
            self.s3_client.delete_object(
                Bucket=settings.S3_BUCKET,
                Key=key
            )
            logger.info(f"Deleted file from S3: {key}")
        except ClientError as e:
            logger.error(f"S3 delete error: {e}")
    
    async def _delete_from_local(self, file_url: str):
        """Delete file from local storage"""
        try:
            file_path = self.local_storage_path / file_url.replace("/storage/", "")
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted local file: {file_path}")
        except Exception as e:
            logger.error(f"Local delete error: {e}")


# Global storage instance
storage_service = StorageService()


async def upload_file_to_storage(file: UploadFile, user_id: int, file_type: str) -> str:
    """Helper function to upload file"""
    return await storage_service.upload_file(file, user_id, file_type)
