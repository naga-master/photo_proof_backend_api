"""Notification model."""

from sqlalchemy import Column, String, ForeignKey, Boolean, Text, Integer, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base, TimestampMixin


class Notification(Base, TimestampMixin):
    """User notification - unified schema for all notification types."""

    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Recipient - either user_id (studio users) or client_id (clients)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Category & Event Type (new unified schema)
    category = Column(String(30), nullable=True, index=True)  # 'upload', 'comment', 'order', 'contract', 'payment', 'system'
    event_type = Column(String(50), nullable=True)  # 'upload_complete', 'comment_new', 'order_placed', etc.
    
    # Legacy type field (kept for backward compatibility)
    type = Column(String(50), nullable=False, index=True, default='system')
    # Types: 'comment', 'favorite', 'order', 'payment', 'system', 'upload'
    
    # Content
    title = Column(String(255), nullable=True)  # "Upload Complete", "New Comment"
    message = Column(String(500), nullable=True)  # "87/101 files uploaded to Wedding 2024"
    text = Column(String(500), nullable=True)  # Legacy field
    context = Column(String(500), nullable=True)  # Legacy field
    timestamp = Column(String(100), nullable=True)  # Human-readable
    
    # Status
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    priority = Column(String(10), nullable=True, default='normal')  # 'low', 'normal', 'high'
    
    # Optional avatar for person-related notifications
    avatar_url = Column(String(500), nullable=True)
    
    # Entity tracking for navigation
    entity_type = Column(String(30), nullable=True)  # 'photo', 'order', 'contract', 'invoice'
    entity_id = Column(String(100), nullable=True)
    
    # Legacy entity fields (kept for backward compatibility)
    related_entity_type = Column(String(50), nullable=True)
    related_entity_id = Column(String(100), nullable=True)
    
    # Related entities for navigation
    project_id = Column(Integer, nullable=True, index=True)
    photo_id = Column(Integer, nullable=True)
    comment_id = Column(Integer, nullable=True)
    
    # Actor info (who triggered the notification)
    actor_name = Column(String(255), nullable=True)
    actor_type = Column(String(20), nullable=True)  # 'studio', 'client', 'system'
    
    # Flexible data for category-specific info (JSON)
    extra_data = Column(JSON, nullable=True)
    # For upload: {"total": 101, "success": 87, "failed": 14, "status": "partial"}
    # For order: {"order_id": "123", "total": 500, "items": 3}
    
    # Email tracking
    email_enabled = Column(Boolean, default=True)
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime, nullable=True)
    
    # Auto-cleanup
    expires_at = Column(DateTime, nullable=True, index=True)

    # Relationships
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(id={self.id}, category={self.category}, type={self.type}, user_id={self.user_id}, client_id={self.client_id})>"
