"""Notification schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    """Response schema for a notification."""
    id: str
    type: str  # 'comment', 'favorite', 'order', 'payment', 'system'
    text: str
    context: str
    timestamp: str
    is_read: bool
    avatar_url: Optional[str] = None
    
    # Related entities for navigation
    project_id: Optional[int] = None
    photo_id: Optional[int] = None
    comment_id: Optional[int] = None
    
    # Actor info
    actor_name: Optional[str] = None
    actor_type: Optional[str] = None  # 'studio' or 'client'
    
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Response schema for notification list."""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int


class NotificationCountResponse(BaseModel):
    """Response schema for unread notification count."""
    unread_count: int


class MarkReadResponse(BaseModel):
    """Response after marking notification(s) as read."""
    success: bool
    message: str
