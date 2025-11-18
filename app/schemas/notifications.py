"""Notification and alert schemas."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class NotificationType(str):
    """Notification type enum values."""
    PROJECT_UPDATE = "project_update"
    CLIENT_MESSAGE = "client_message"
    PAYMENT_RECEIVED = "payment_received"
    INVOICE_OVERDUE = "invoice_overdue"
    GALLERY_VIEWED = "gallery_viewed"
    SYSTEM_ALERT = "system_alert"
    WORKFLOW_REMINDER = "workflow_reminder"


class NotificationPriority(str):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationRead(BaseModel):
    """Notification read schema."""
    id: str
    user_id: str
    type: str
    title: str
    message: str
    priority: str
    data: Optional[Dict[str, Any]] = None
    is_read: bool = False
    is_archived: bool = False
    action_url: Optional[str] = None
    created_at: datetime
    read_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Alias for backward compatibility  
Notification = NotificationRead


class NotificationStatus(str):
    """Notification status values."""
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"


class NotificationRequest(BaseModel):
    """Request to create a notification."""
    user_id: str
    type: str
    title: str
    message: str
    priority: str = NotificationPriority.MEDIUM
    data: Optional[Dict[str, Any]] = None
    action_url: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class NotificationTemplate(BaseModel):
    """Notification template for automated messages."""
    id: str
    name: str
    subject: str
    content: str
    type: str
    variables: List[str]
    is_active: bool = True


class MessageThread(BaseModel):
    """Message thread between studio and client."""
    id: str
    studio_id: str
    client_id: str
    project_id: Optional[str] = None
    subject: str
    status: str = "active"
    last_message_at: Optional[datetime] = None
    unread_count: int = 0
    created_at: datetime
    updated_at: datetime


class MessageRequest(BaseModel):
    """Request to send a message."""
    content: str
    attachments: Optional[List[str]] = None


class NotificationPreferences(BaseModel):
    """User notification preferences."""
    user_id: str
    email_notifications: bool = True
    push_notifications: bool = True
    sms_notifications: bool = False
    notification_types: Dict[str, bool] = {}
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    updated_at: datetime


class CreateNotificationRequest(BaseModel):
    """Request to create a notification."""
    user_id: str
    type: str
    title: str
    message: str
    priority: str = NotificationPriority.MEDIUM
    data: Optional[Dict[str, Any]] = None
    action_url: Optional[str] = None


class NotificationSettings(BaseModel):
    """User notification preferences."""
    id: str
    user_id: str
    email_enabled: bool = True
    push_enabled: bool = True
    sms_enabled: bool = False
    notification_types: Dict[str, bool]  # type -> enabled
    quiet_hours_start: Optional[str] = None  # HH:MM format
    quiet_hours_end: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UpdateNotificationSettingsRequest(BaseModel):
    """Request to update notification settings."""
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    notification_types: Optional[Dict[str, bool]] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class NotificationListResponse(BaseModel):
    """Response for notification list."""
    notifications: List[NotificationRead]
    unread_count: int
    total_count: int


class BulkNotificationAction(BaseModel):
    """Bulk action on notifications."""
    notification_ids: List[str]
    action: str  # 'mark_read', 'mark_unread', 'archive', 'delete'


class NotificationSummary(BaseModel):
    """Notification summary for dashboard."""
    total_unread: int
    priority_breakdown: Dict[str, int]
    recent_notifications: List[NotificationRead]
    trending_types: List[Dict[str, Any]]