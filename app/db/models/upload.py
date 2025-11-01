"""Upload session and token models for presigned URL system."""

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID
import uuid
import secrets

from .base import Base, TimestampMixin


class UploadSession(Base, TimestampMixin):
    """Temporary upload session for wizard workflow."""

    __tablename__ = "upload_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Mode: creating new project or adding to existing
    mode = Column(String(50), nullable=False)  # 'new' or 'existing'
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    
    # Wizard data stored as JSON
    project_details = Column(JSON, nullable=True)  # Project setup info
    folder_map = Column(JSON, nullable=True)  # Array of folder mappings
    upload_rules = Column(JSON, nullable=True)  # Upload configuration
    
    # Session status
    status = Column(String(50), nullable=False, default='in_progress')
    # Statuses: 'in_progress', 'completed', 'failed'
    
    # Expiry
    expires_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(hours=24))

    # Relationships
    user = relationship("User")
    project = relationship("Project")
    upload_tokens = relationship("UploadToken", back_populates="upload_session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<UploadSession(id={self.id}, user_id={self.user_id}, status={self.status})>"


class UploadToken(Base, TimestampMixin):
    """Presigned upload token for individual file upload."""

    __tablename__ = "upload_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token = Column(String(64), nullable=False, unique=True, index=True, default=lambda: secrets.token_hex(32))
    
    upload_session_id = Column(String(36), ForeignKey("upload_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # File info
    filename = Column(String(500), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    
    # Destination
    photo_id = Column(Integer, ForeignKey("photos.id", ondelete="SET NULL"), nullable=True)
    storage_path = Column(String(1000), nullable=True)
    
    # Token status
    status = Column(String(50), nullable=False, default='pending')
    # Statuses: 'pending', 'uploading', 'completed', 'failed'
    
    # Expiry (short-lived - 15 minutes)
    expires_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(minutes=15))

    # Relationships
    upload_session = relationship("UploadSession", back_populates="upload_tokens")
    photo = relationship("Photo")

    def is_expired(self):
        """Check if token has expired."""
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f"<UploadToken(id={self.id}, token={self.token[:8]}..., status={self.status})>"
