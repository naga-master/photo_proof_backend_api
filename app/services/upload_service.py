"""Upload service with presigned URL token management."""

import logging
import secrets
import time
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict
from sqlalchemy.orm import Session
from PIL import Image
import io
from pathlib import Path

from app.db.models import UploadSession, UploadToken, Photo, Project
from app.services.storage_service import StorageService

from fastapi import HTTPException

logger = logging.getLogger(__name__)


class UploadService:
    """Photo upload service with presigned URLs."""
    
    def __init__(self, storage_service: StorageService):
        self.storage = storage_service
    
    @staticmethod
    def calculate_file_hash(file_data: bytes) -> str:
        """Calculate SHA-256 hash of file content for duplicate detection."""
        return hashlib.sha256(file_data).hexdigest()
    
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
        
        # Create storage path (originals/ subdirectory for nested structure)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = filename.replace(" ", "_")
        storage_path = f"projects/{project_id}/originals/{timestamp}_{token[:8]}_{safe_filename}"
        
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
        Complete upload using token and create Photo record or PhotoVersion.
        Routes to version creation if is_version_upload flag is set.
        """
        # Validate token
        upload_token = db.query(UploadToken).filter(
            UploadToken.token == token,
            UploadToken.status == 'pending',
            UploadToken.expires_at > datetime.utcnow(),
        ).first()
        
        if not upload_token:
            raise ValueError("Invalid or expired upload token")
        
        # Check if this is a version upload
        if upload_token.is_version_upload:
            return await self._complete_version_upload(db, upload_token, file_data)
        else:
            return await self._complete_new_photo_upload(db, upload_token, file_data)
    
    async def _complete_version_upload(
        self,
        db: Session,
        upload_token: UploadToken,
        file_data: bytes,
    ) -> Photo:
        """
        Complete version upload - creates new version for existing photo.
        """
        from app.services.version_service import VersionService
        
        # Get target photo
        photo = db.query(Photo).filter(
            Photo.id == upload_token.target_photo_id
        ).first()
        
        if not photo:
            raise ValueError(f"Target photo {upload_token.target_photo_id} not found")
        
        # Get upload session for user_id
        upload_session = db.query(UploadSession).filter(
            UploadSession.id == upload_token.upload_session_id
        ).first()
        
        if not upload_session:
            raise ValueError("Upload session not found")
        
        # Create version using version service
        version_service = VersionService(db, self.storage)
        
        logger.info(f"Creating version for photo {photo.id}", extra={
            "photo_id": photo.id,
            "upload_filename": upload_token.filename,
            "version_label": upload_token.version_label,
            "mapping_type": upload_token.mapping_type
        })
        
        photo_version = await version_service.create_version(
            photo_id=photo.id,
            file_data=file_data,
            filename=upload_token.filename,
            uploaded_by=upload_session.user_id,
            version_label=upload_token.version_label,
            upload_note=f"Uploaded via {upload_token.mapping_type or 'manual'} mapping"
        )
        
        # Mark token as completed
        upload_token.status = 'completed'
        upload_token.photo_id = photo.id  # Reference original photo
        
        # Set photo status to processing
        photo.status = 'processing'
        
        db.commit()
        db.refresh(photo)
        
        logger.info(f"Version {photo_version.version_number} created for photo {photo.id}, queuing for background processing")
        
        # Note: Background processing will be triggered by the router
        # Variants for photo versions will be generated in background
        
        # Return photo (not photo_version) for consistent API response
        return photo
    
    async def _complete_new_photo_upload(
        self,
        db: Session,
        upload_token: UploadToken,
        file_data: bytes,
    ) -> Photo:
        """
        Complete new photo upload - creates new Photo record.
        """
        
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
            logger.warning(f"[UploadService] Warning: Could not extract dimensions for {upload_token.filename}: {str(e)}")
            logger.warning(f"[UploadService] File size: {len(file_data)} bytes, Content-Type: {upload_token.content_type}")
            
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
        
        # Calculate file hash for duplicate detection
        file_hash = self.calculate_file_hash(file_data)
        
        # Check for duplicate content in same folder (not project-wide)
        # Same photo can exist in different folders (different contexts)
        if upload_token.folder_id:
            duplicate_photo = db.query(Photo).filter(
                Photo.project_id == project.id,
                Photo.folder_id == upload_token.folder_id,
                Photo.content_hash == file_hash
            ).first()
            
            if duplicate_photo:
                # Get folder name for better error message
                from app.db.models.project import Folder
                folder = db.query(Folder).filter(Folder.id == upload_token.folder_id).first()
                folder_name = folder.name if folder else "this folder"
                
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "duplicate_detected",
                        "type": "photo_content",
                        "message": f"This photo already exists in folder '{folder_name}'",
                        "existing_photo": {
                            "id": duplicate_photo.id,
                            "filename": duplicate_photo.original_filename,
                            "folder_name": folder_name,
                            "uploaded_at": duplicate_photo.created_at.isoformat(),
                            "thumbnail_url": f"/api/photos/{duplicate_photo.id}/thumbnail"
                        }
                    }
                )
        else:
            # For photos without folders, check at project level
            duplicate_photo = db.query(Photo).filter(
                Photo.project_id == project.id,
                Photo.folder_id.is_(None),
                Photo.content_hash == file_hash
            ).first()
            
            if duplicate_photo:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "duplicate_detected",
                        "type": "photo_content",
                        "message": "This photo already exists in this project (no folder)",
                        "existing_photo": {
                            "id": duplicate_photo.id,
                            "filename": duplicate_photo.original_filename,
                            "uploaded_at": duplicate_photo.created_at.isoformat(),
                            "thumbnail_url": f"/api/photos/{duplicate_photo.id}/thumbnail"
                        }
                    }
                )
        
        # Check for same filename in same folder - BLOCK if duplicate
        # Photos must have unique filenames within their folder (or within project if no folder)
        if upload_token.folder_id:
            # Check for duplicate filename in the same folder
            same_filename = db.query(Photo).filter(
                Photo.project_id == project.id,
                Photo.folder_id == upload_token.folder_id,
                Photo.original_filename == upload_token.filename
            ).first()
            
            if same_filename:
                # Get folder name for better error message
                from app.db.models.project import Folder
                folder = db.query(Folder).filter(Folder.id == upload_token.folder_id).first()
                folder_name = folder.name if folder else "this folder"
                
                logger.warning(
                    f"Duplicate filename in folder {upload_token.folder_id}: "
                    f"{upload_token.filename} (existing ID: {same_filename.id})"
                )
                
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "duplicate_detected",
                        "type": "photo_filename",
                        "message": f"File '{upload_token.filename}' already exists in folder '{folder_name}'. Please rename the file.",
                        "existing_photo": {
                            "id": same_filename.id,
                            "filename": same_filename.original_filename,
                            "folder_name": folder_name,
                            "uploaded_at": same_filename.created_at.isoformat()
                        }
                    }
                )
        else:
            # Check for duplicate filename in project (no folder)
            same_filename = db.query(Photo).filter(
                Photo.project_id == project.id,
                Photo.folder_id.is_(None),
                Photo.original_filename == upload_token.filename
            ).first()
            
            if same_filename:
                logger.warning(
                    f"Duplicate filename in project {project.id} (no folder): "
                    f"{upload_token.filename} (existing ID: {same_filename.id})"
                )
                
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "duplicate_detected",
                        "type": "photo_filename",
                        "message": f"File '{upload_token.filename}' already exists in this project. Please rename the file.",
                        "existing_photo": {
                            "id": same_filename.id,
                            "filename": same_filename.original_filename,
                            "uploaded_at": same_filename.created_at.isoformat()
                        }
                    }
                )
        
        # Save file to storage
        file_obj = io.BytesIO(file_data)
        url = await self.storage.save_file(file_obj, upload_token.storage_path)
        
        # Create Photo record with 'processing' status
        # Variants will be generated in background
        photo = Photo(
            project_id=upload_session.project_id,
            folder_id=upload_token.folder_id,
            original_filename=upload_token.filename,
            storage_path=upload_token.storage_path,
            src=url,
            alt=upload_token.filename,
            width=width,
            height=height,
            file_size=upload_token.file_size,
            mime_type=upload_token.content_type,
            uploaded_by=upload_session.user_id,
            status='processing',  # Changed from 'completed' - variants generated in background
            content_hash=file_hash,  # For duplicate detection
        )
        
        db.add(photo)
        
        # Mark token as completed
        upload_token.status = 'completed'
        upload_token.photo_id = photo.id
        
        # Flush to make the photo visible to subsequent queries
        db.flush()
        
        # Update project photo count
        # Count all photos with status='completed' (the default status for successfully uploaded photos)
        project.photo_count = db.query(Photo).filter(
            Photo.project_id == project.id,
            Photo.status == "completed"
        ).count()
        
        # Set project cover photo if not already set
        if not project.cover_photo_id:
            project.cover_photo_id = photo.id
            logger.info(f"Set project cover photo", extra={
                "project_id": project.id,
                "photo_id": photo.id
            })
        
        # Update folder photo count and set cover photo if this photo belongs to a folder
        if upload_token.folder_id:
            from app.db.models.project import Folder
            folder = db.query(Folder).filter(Folder.id == upload_token.folder_id).first()
            if folder:
                # Update folder photo count
                folder.photo_count = db.query(Photo).filter(
                    Photo.folder_id == folder.id,
                    Photo.status == "completed"
                ).count()
                
                # Set cover photo if folder doesn't have one yet
                if not folder.cover_photo_id:
                    folder.cover_photo_id = photo.id
                    logger.info(f"Set folder cover photo", extra={
                        "folder_id": folder.id,
                        "photo_id": photo.id
                    })
        
        # Commit photo record immediately - variants will be generated in background
        db.commit()
        db.refresh(photo)
        
        logger.info(f"Photo {photo.id} uploaded successfully, queuing for background processing")
        
        # Note: Background processing will be triggered by the router using BackgroundTasks
        # The _process_photo_variants_background function will:
        # 1. Generate quality variants
        # 2. Generate ThumbHash
        # 3. Update status to 'completed' or set processing_error
        
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
            
            # Create storage path (originals/ subdirectory for nested structure)
            filename = file_info.get('filename', f'file_{idx}')
            safe_filename = filename.replace(" ", "_")
            storage_path = f"projects/{project_id}/originals/{timestamp}_{token[:8]}_{safe_filename}"
            
            # Create upload token record
            upload_token = UploadToken(
                token=token,
                upload_session_id=upload_session.id,
                filename=filename,
                storage_path=storage_path,
                content_type=file_info.get('content_type', 'image/jpeg'),
                file_size=file_info.get('file_size', 0),
                folder_id=folder_id,
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


def _process_photo_variants_background(
    photo_id: int,
    storage_path: str,
    project_id: int,
    max_retries: int = 3
):
    """
    Background task to generate variants with retry logic.
    This runs asynchronously after photo upload completes.
    """
    from app.db.session import SessionLocal
    from app.services.image_processing_service import ImageProcessingService
    from app.services.storage_service import get_storage_service
    
    db = SessionLocal()
    try:
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            logger.error(f"Photo {photo_id} not found for variant processing")
            return
        
        storage = get_storage_service()
        image_service = ImageProcessingService()
        storage_full_path = storage.get_full_path(storage_path)
        
        # Retry loop with exponential backoff
        last_error = None
        for attempt in range(max_retries):
            try:
                photo.processing_attempts = attempt + 1
                photo.last_processing_attempt_at = datetime.utcnow()
                db.commit()
                
                logger.info(f"Generating variants for photo {photo_id} (attempt {attempt + 1}/{max_retries})")
                
                # Generate quality variants
                variants = image_service.generate_quality_variants(
                    db=db,
                    photo=photo,
                    original_file_path=storage_full_path
                )
                
                # Generate ThumbHash
                thumbhash = image_service.generate_thumbhash(storage_full_path)
                if thumbhash:
                    photo.thumbhash = thumbhash
                
                # SUCCESS - mark as completed
                photo.status = 'completed'
                photo.processing_error = None
                db.commit()
                logger.info(f"Successfully generated variants for photo {photo_id}")
                return
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Variant generation attempt {attempt + 1} failed for photo {photo_id}: {e}")
                
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    time.sleep(2 ** attempt)
        
        # All retries failed - still mark as completed but with error
        photo.status = 'completed'  # Photo is still usable with original
        photo.processing_error = f"Failed after {max_retries} attempts: {last_error}"
        db.commit()
        logger.error(f"Failed to generate variants for photo {photo_id} after {max_retries} attempts: {last_error}")
        
    except Exception as e:
        logger.error(f"Critical error in background processing for photo {photo_id}: {e}")
        try:
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if photo:
                photo.status = 'completed'
                photo.processing_error = f"Critical error: {str(e)}"
                db.commit()
        except:
            pass
    finally:
        db.close()
