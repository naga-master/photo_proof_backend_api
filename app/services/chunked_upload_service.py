"""
Chunked Upload Service

Handles server-side chunked file uploads with assembly and validation.
"""

import hashlib
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid

from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.db.models import Photo, Project
from app.services.storage_service import StorageService


logger = logging.getLogger(__name__)


# Global session store (shared across all service instances)
# TODO: In production, migrate to Redis or database for persistence
_SESSIONS: Dict[str, 'ChunkUploadSession'] = {}


class ChunkUploadSession:
    """Represents an active chunk upload session"""
    
    def __init__(
        self,
        session_id: str,
        filename: str,
        file_size: int,
        mime_type: str,
        project_id: int,
        folder_id: Optional[str],
        user_id: str,
        total_chunks: int,
    ):
        self.session_id = session_id
        self.filename = filename
        self.file_size = file_size
        self.mime_type = mime_type
        self.project_id = project_id
        self.folder_id = folder_id
        self.user_id = user_id
        self.total_chunks = total_chunks
        self.uploaded_chunks: List[int] = []
        self.chunk_hashes: Dict[int, str] = {}
        self.created_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(hours=24)
        self.status = 'uploading'


class ChunkedUploadService:
    """Service for handling chunked file uploads"""
    
    def __init__(self, storage_service: StorageService):
        self.storage = storage_service
        self.temp_dir = Path("data/uploads/chunks")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def initialize_session(
        self,
        db: Session,
        filename: str,
        file_size: int,
        mime_type: str,
        project_id: int,
        folder_id: Optional[str],
        user_id: str,
        total_chunks: int,
    ) -> ChunkUploadSession:
        """Initialize a new chunked upload session"""
        
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create session
        session = ChunkUploadSession(
            session_id=session_id,
            filename=filename,
            file_size=file_size,
            mime_type=mime_type,
            project_id=project_id,
            folder_id=folder_id,
            user_id=user_id,
            total_chunks=total_chunks,
        )
        
        # Store session
        _SESSIONS[session_id] = session
        
        # Create temp directory for this session
        session_dir = self.temp_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"[ChunkedUpload] Session initialized: {session_id}")
        logger.debug(f"  Filename: {filename}")
        logger.debug(f"  Size: {file_size} bytes")
        logger.debug(f"  Total chunks: {total_chunks}")
        
        return session
    
    async def receive_chunk(
        self,
        session_id: str,
        chunk_index: int,
        chunk_data: bytes,
        chunk_hash: Optional[str] = None,
    ) -> Dict:
        """Receive and store a chunk"""
        
        # Get session
        session = _SESSIONS.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Check if session expired
        if datetime.utcnow() > session.expires_at:
            raise ValueError(f"Session {session_id} expired")
        
        # Verify chunk index
        if chunk_index < 0 or chunk_index >= session.total_chunks:
            raise ValueError(f"Invalid chunk index {chunk_index}")
        
        # Check if chunk already uploaded
        if chunk_index in session.uploaded_chunks:
            logger.debug(f"[ChunkedUpload] Chunk {chunk_index} already uploaded, skipping")
            return {
                "session_id": session_id,
                "chunk_index": chunk_index,
                "status": "already_uploaded"
            }
        
        # Verify hash if provided
        if chunk_hash:
            actual_hash = hashlib.sha256(chunk_data).hexdigest()
            if actual_hash != chunk_hash:
                raise ValueError(f"Chunk {chunk_index} hash mismatch")
            session.chunk_hashes[chunk_index] = actual_hash
        
        # Save chunk to temp storage
        chunk_path = self.temp_dir / session_id / f"chunk_{chunk_index:04d}"
        with open(chunk_path, 'wb') as f:
            f.write(chunk_data)
        
        # Mark as uploaded
        session.uploaded_chunks.append(chunk_index)
        session.uploaded_chunks.sort()
        
        logger.debug(f"[ChunkedUpload] Chunk {chunk_index} received ({len(chunk_data)} bytes)")
        logger.debug(f"  Progress: {len(session.uploaded_chunks)}/{session.total_chunks}")
        
        return {
            "session_id": session_id,
            "chunk_index": chunk_index,
            "status": "received",
            "uploaded_chunks": len(session.uploaded_chunks),
            "total_chunks": session.total_chunks,
        }
    
    async def finalize_upload(
        self,
        db: Session,
        session_id: str,
    ) -> Photo:
        """Finalize upload by assembling chunks and creating Photo record"""
        
        # Get session
        session = _SESSIONS.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Verify all chunks uploaded
        if len(session.uploaded_chunks) != session.total_chunks:
            missing = set(range(session.total_chunks)) - set(session.uploaded_chunks)
            raise ValueError(f"Missing chunks: {missing}")
        
        logger.debug(f"[ChunkedUpload] Finalizing upload: {session_id}")
        
        # Assemble chunks
        final_path = self.temp_dir / session_id / "final"
        with open(final_path, 'wb') as outfile:
            for chunk_index in range(session.total_chunks):
                chunk_path = self.temp_dir / session_id / f"chunk_{chunk_index:04d}"
                with open(chunk_path, 'rb') as infile:
                    outfile.write(infile.read())
        
        # Verify final file size
        actual_size = final_path.stat().st_size
        if actual_size != session.file_size:
            raise ValueError(f"Assembled file size mismatch: expected {session.file_size}, got {actual_size}")
        
        logger.debug(f"[ChunkedUpload] File assembled successfully ({actual_size} bytes)")
        
        # Extract image dimensions
        from PIL import Image
        import io
        
        with open(final_path, 'rb') as f:
            image_data = f.read()
        
        try:
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
        except Exception as e:
            logger.debug(f"[ChunkedUpload] Warning: Could not extract dimensions: {e}")
            width, height = 1920, 1080  # Default
        
        # Save to permanent storage (originals/ subdirectory for nested structure)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = session.filename.replace(" ", "_")
        storage_path = f"projects/{session.project_id}/originals/{timestamp}_{session_id[:8]}_{safe_filename}"
        
        # Upload to storage
        with open(final_path, 'rb') as f:
            url = await self.storage.save_file(f, storage_path)
        
        logger.debug(f"[ChunkedUpload] File saved to storage: {storage_path}")
        
        # Create Photo record
        photo = Photo(
            project_id=session.project_id,
            folder_id=session.folder_id,
            original_filename=session.filename,
            storage_path=storage_path,
            src=url,
            alt=session.filename,
            width=width,
            height=height,
            file_size=session.file_size,
            mime_type=session.mime_type,
            uploaded_by=session.user_id,
            status='completed',
        )
        
        db.add(photo)
        db.flush()
        
        # Update project photo count
        project = db.query(Project).filter(Project.id == session.project_id).first()
        if project:
            project.photo_count = db.query(Photo).filter(
                Photo.project_id == project.id,
                Photo.status == "completed"
            ).count()
            
            # Set cover photo if not set
            if not project.cover_photo_id:
                project.cover_photo_id = photo.id
        
        # Generate quality variants (Phase 2: Backend Image Optimization)
        from app.services.image_processing_service import ImageProcessingService
        
        image_service = ImageProcessingService()
        storage_full_path = self.storage.get_full_path(storage_path)
        
        try:
            logger.debug(f"[ChunkedUpload] Generating quality variants for photo {photo.id}")
            variants = await image_service.generate_quality_variants(
                db=db,
                photo=photo,
                original_file_path=storage_full_path
            )
            logger.debug(f"[ChunkedUpload] Generated {len(variants)} variants for photo {photo.id}")
            
            # Generate ThumbHash for instant placeholders
            logger.debug(f"[ChunkedUpload] Generating ThumbHash for photo {photo.id}")
            thumbhash = image_service.generate_thumbhash(storage_full_path)
            if thumbhash:
                photo.thumbhash = thumbhash
                logger.debug(f"[ChunkedUpload] ThumbHash generated for photo {photo.id}")
            
        except Exception as e:
            # Don't fail upload if variant generation fails
            logger.debug(f"[ChunkedUpload] Failed to generate variants for photo {photo.id}: {e}")
            # Variants can be regenerated later via admin task
        
        db.commit()
        db.refresh(photo)
        
        # Cleanup temp files
        self.cleanup_session(session_id)
        
        # Remove from sessions
        del _SESSIONS[session_id]
        
        logger.debug(f"[ChunkedUpload] Upload finalized, photo ID: {photo.id}")
        
        return photo
    
    def get_session(self, session_id: str) -> Optional[ChunkUploadSession]:
        """Get session details"""
        return _SESSIONS.get(session_id)
    
    def cleanup_session(self, session_id: str) -> None:
        """Cleanup temporary files for a session"""
        session_dir = self.temp_dir / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir)
            logger.debug(f"[ChunkedUpload] Cleaned up temp files for session: {session_id}")
    
    def cleanup_expired_sessions(self) -> None:
        """Cleanup expired sessions (should be called periodically)"""
        now = datetime.utcnow()
        expired = [
            session_id
            for session_id, session in _SESSIONS.items()
            if now > session.expires_at
        ]
        
        for session_id in expired:
            self.cleanup_session(session_id)
            del _SESSIONS[session_id]
            logger.debug(f"[ChunkedUpload] Expired session cleaned up: {session_id}")
        
        if expired:
            logger.debug(f"[ChunkedUpload] Cleaned up {len(expired)} expired sessions")
