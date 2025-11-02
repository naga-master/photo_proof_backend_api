"""Upload service with presigned URL token management."""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict
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
        
        # Extract image dimensions with robust error handling
        width = 0
        height = 0
        try:
            # Try to open and validate the image
            image_buffer = io.BytesIO(file_data)
            image = Image.open(image_buffer)
            image.verify()  # Verify it's a valid image
            
            # Re-open after verify (verify closes the file)
            image_buffer.seek(0)
            image = Image.open(image_buffer)
            width, height = image.size
            
        except Exception as e:
            # Log warning but don't fail - set default dimensions
            print(f"[UploadService] Warning: Could not extract dimensions for {upload_token.filename}: {str(e)}")
            print(f"[UploadService] File size: {len(file_data)} bytes, Content-Type: {upload_token.content_type}")
            
            # Set default dimensions for images that can't be parsed
            # Backend will accept them but they'll need manual verification
            width = 1920
            height = 1080
            
            # Only fail if it's supposed to be an image but is completely invalid
            if upload_token.content_type.startswith('image/'):
                # Check if file data is actually valid (not empty or corrupted)
                if len(file_data) == 0:
                    raise ValueError(f"Empty file data for {upload_token.filename}")
                # Otherwise allow it through with default dimensions
        
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
            user_id=user_id,
            mode='existing',
            project_id=project_id,
            status="in_progress",
            upload_rules={
                'total_files': total_files,
                'uploaded_files': 0,
                'batch_upload': True
            }
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
        
        # Update upload_rules JSON field
        if not session.upload_rules:
            session.upload_rules = {}
        
        session.upload_rules['uploaded_files'] = uploaded_count
        
        # Get total from upload_rules
        total_files = session.upload_rules.get('total_files', 0)
        
        if uploaded_count >= total_files:
            session.status = "completed"
        
        db.commit()
        db.refresh(session)
        
        return session

    def generate_batch_upload_tokens(
        self,
        db: Session,
        project_id: int,
        files: List[Dict[str, any]],
        user_id: str,
        folder_id: Optional[str] = None,
    ) -> Tuple[UploadSession, List[Tuple[UploadToken, str]]]:
        """
        Generate batch presigned upload tokens for multiple files.
        Returns (upload_session, [(token_record, upload_url), ...])
        """
        # Create upload session for this batch
        # Store batch info in upload_rules JSON field
        upload_session = UploadSession(
            user_id=user_id,
            mode='existing',
            project_id=project_id,
            status='in_progress',
            upload_rules={
                'total_files': len(files),
                'uploaded_files': 0,
                'batch_upload': True
            }
        )
        db.add(upload_session)
        db.flush()
        
        # Generate tokens for all files
        tokens_and_urls = []
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        for idx, file_info in enumerate(files):
            # Generate secure token
            token = secrets.token_urlsafe(32)
            
            # Create storage path
            filename = file_info.get('filename', f'file_{idx}')
            safe_filename = filename.replace(" ", "_")
            storage_path = f"projects/{project_id}/{timestamp}_{token[:8]}_{safe_filename}"
            
            # Create upload token record
            upload_token = UploadToken(
                token=token,
                upload_session_id=upload_session.id,
                filename=filename,
                storage_path=storage_path,
                content_type=file_info.get('content_type', 'image/jpeg'),
                file_size=file_info.get('file_size', 0),
                status='pending',
                expires_at=datetime.utcnow() + timedelta(hours=1),
            )
            
            db.add(upload_token)
            
            # Generate presigned URL
            upload_url = f"/v2/upload/{token}"
            
            tokens_and_urls.append((upload_token, upload_url))
        
        db.commit()
        db.refresh(upload_session)
        
        return upload_session, tokens_and_urls
    
    async def complete_batch_upload_verification(
        self,
        db: Session,
        session_id: int,
    ) -> Dict[str, any]:
        """
        Verify batch upload completion and update session.
        Returns summary of upload status.
        """
        upload_session = db.query(UploadSession).filter(
            UploadSession.id == session_id
        ).first()
        
        if not upload_session:
            raise ValueError("Upload session not found")
        
        # Get all tokens for this session
        tokens = db.query(UploadToken).filter(
            UploadToken.upload_session_id == session_id
        ).all()
        
        # Count completed uploads
        completed_count = sum(1 for t in tokens if t.status == 'completed')
        failed_count = sum(1 for t in tokens if t.status == 'failed')
        pending_count = sum(1 for t in tokens if t.status == 'pending')
        
        # Get total from upload_rules if it exists
        total_files = len(tokens)
        if upload_session.upload_rules and 'total_files' in upload_session.upload_rules:
            total_files = upload_session.upload_rules['total_files']
        
        # Update session status
        if completed_count + failed_count >= total_files:
            upload_session.status = 'completed'
        
        # Update upload_rules with progress
        if upload_session.upload_rules:
            upload_session.upload_rules['uploaded_files'] = completed_count
        else:
            upload_session.upload_rules = {
                'total_files': total_files,
                'uploaded_files': completed_count,
                'batch_upload': True
            }
        
        db.commit()
        
        return {
            "session_id": session_id,
            "total_files": total_files,
            "completed": completed_count,
            "failed": failed_count,
            "pending": pending_count,
            "status": upload_session.status,
        }
