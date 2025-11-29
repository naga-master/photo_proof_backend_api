"""Notification schemas."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    """Response schema for a notification."""
    id: str
    type: str  # 'comment', 'favorite', 'order', 'payment', 'system', 'upload'
    text: Optional[str] = None
    context: Optional[str] = None
    timestamp: str
    is_read: bool
    avatar_url: Optional[str] = None
    
    # New unified fields
    category: Optional[str] = None
    event_type: Optional[str] = None
    title: Optional[str] = None
    message: Optional[str] = None
    priority: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    
    # Related entities for navigation
    project_id: Optional[int] = None
    photo_id: Optional[int] = None
    comment_id: Optional[int] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    
    # Actor info
    actor_name: Optional[str] = None
    actor_type: Optional[str] = None  # 'studio', 'client', or 'system'
    
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UploadNotificationRequest(BaseModel):
    """Request schema for creating an upload notification."""
    project_id: int
    project_name: str
    status: str  # 'success', 'partial', 'failed'
    total_files: int
    completed_files: int
    failed_files: int


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
