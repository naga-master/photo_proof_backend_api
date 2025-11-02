"""Upload service with presigned URL token management."""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from PIL import Image
import io

from app.db.models import UploadSession, UploadToken, Photo, Project
from app.services.storage_service import StorageService


class UploadService:
    """Photo upload service with presigned URLs."""
    
    def __init__(self, storage_service: StorageService):
        self.storage = storage_service
    
    def generate_upload_token(
        self,
        db: Session,
        project_id: int,
        filename: str,
        content_type: str,
        file_size: int,
        user_id: str,
        folder_id: Optional[str] = None,
    ) -> Tuple[UploadToken, str]:
        """
        Generate presigned upload token.
        Returns (token_record, upload_url)
        """
        # First, create or get upload session for this project
        upload_session = db.query(UploadSession).filter(
            UploadSession.user_id == user_id,
            UploadSession.project_id == project_id,
            UploadSession.status == 'in_progress'
        ).first()
        
        if not upload_session:
            upload_session = UploadSession(
                user_id=user_id,
                mode='existing',
                project_id=project_id,
                status='in_progress',
            )
            db.add(upload_session)
            db.flush()
        
        # Generate secure token
        token = secrets.token_urlsafe(32)
        
        # Create storage path
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = filename.replace(" ", "_")
        storage_path = f"projects/{project_id}/{timestamp}_{token[:8]}_{safe_filename}"
        
        # Create upload token record with correct fields
        upload_token = UploadToken(
            token=token,
            upload_session_id=upload_session.id,
            filename=filename,
            storage_path=storage_path,
            content_type=content_type,
            file_size=file_size,
            status='pending',
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        
        db.add(upload_token)
        db.commit()
        db.refresh(upload_token)
        
        # Generate presigned URL
        upload_url = f"/v2/upload/{token}"
        
        return upload_token, upload_url
    
    async def complete_upload(
        self,
        db: Session,
        token: str,
        file_data: bytes,
    ) -> Photo:
        """
        Complete upload using token and create Photo record.
        """
        # Validate token
        upload_token = db.query(UploadToken).filter(
            UploadToken.token == token,
            UploadToken.status == 'pending',
            UploadToken.expires_at > datetime.utcnow(),
        ).first()
        
        if not upload_token:
            raise ValueError("Invalid or expired upload token")
        
        # Get upload session to find project_id
        upload_session = db.query(UploadSession).filter(
            UploadSession.id == upload_token.upload_session_id
        ).first()
        
        if not upload_session or not upload_session.project_id:
            raise ValueError("Upload session or project not found")
        
        # Validate project exists
        project = db.query(Project).filter(Project.id == upload_session.project_id).first()
        if not project:
            raise ValueError("Project not found")
        
        # Extract image dimensions
        try:
            image = Image.open(io.BytesIO(file_data))
            width, height = image.size
        except Exception as e:
            raise ValueError(f"Invalid image file: {str(e)}")
        
        # Save file to storage
        file_obj = io.BytesIO(file_data)
        url = await self.storage.save_file(file_obj, upload_token.storage_path)
        
        # Create Photo record
        photo = Photo(
            project_id=upload_session.project_id,
            folder_id=None,
            original_filename=upload_token.filename,
            storage_path=upload_token.storage_path,
            src=url,
            alt=upload_token.filename,
            width=width,
            height=height,
            file_size=upload_token.file_size,
            mime_type=upload_token.content_type,
            uploaded_by=upload_session.user_id,
            status='completed',
        )
        
        db.add(photo)
        
        # Mark token as completed
        upload_token.status = 'completed'
        upload_token.photo_id = photo.id
        
        # Update project photo count
        project.photo_count = db.query(Photo).filter(
            Photo.project_id == project.id,
            Photo.status == "active"
        ).count() + 1
        
        db.commit()
        db.refresh(photo)
        
        return photo
    
    def create_upload_session(
        self,
        db: Session,
        project_id: int,
        user_id: str,
        total_files: int,
    ) -> UploadSession:
        """Create batch upload session."""
        session = UploadSession(
            project_id=project_id,
            user_id=user_id,
            total_files=total_files,
            uploaded_files=0,
            status="in_progress",
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return session
    
    def update_upload_progress(
        self,
        db: Session,
        session_id: int,
        uploaded_count: int,
    ) -> UploadSession:
        """Update upload session progress."""
        session = db.query(UploadSession).filter(UploadSession.id == session_id).first()
        
        if not session:
            raise ValueError("Upload session not found")
        
        session.uploaded_files = uploaded_count
        
        if uploaded_count >= session.total_files:
            session.status = "completed"
        
        db.commit()
        db.refresh(session)
        
        return session
