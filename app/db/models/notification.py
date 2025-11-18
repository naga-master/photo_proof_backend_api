"""Notification model."""

from sqlalchemy import Column, String, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base, TimestampMixin


class Notification(Base, TimestampMixin):
    """User notification."""

    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Notification type
    type = Column(String(50), nullable=False, index=True)
    # Types: 'comment', 'favorite', 'order', 'payment', 'system'
    
    # Content
    text = Column(String(500), nullable=False)
    context = Column(String(500), nullable=False)
    timestamp = Column(String(100), nullable=True)  # Human-readable
    
    # Status
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    
    # Optional avatar for person-related notifications
    avatar_url = Column(String(500), nullable=True)
    
    # Optional related entity tracking
    related_entity_type = Column(String(50), nullable=True)  # 'photo', 'order', 'invoice', etc.
    related_entity_id = Column(String(100), nullable=True)

    # Relationships
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type}, user_id={self.user_id})>"
