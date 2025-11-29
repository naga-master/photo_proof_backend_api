"""Notification router for in-app notifications."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.schemas.users import UserRead
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationCountResponse,
    MarkReadResponse,
    UploadNotificationRequest,
)
from app.services.notification_service import NotificationService
from app.services.notification_cleanup_service import NotificationCleanupService


router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def _get_user_and_client_ids(current_user: UserRead) -> tuple[Optional[str], Optional[int]]:
    """Extract user_id and client_id from current user.
    
    For clients using new auth system, id is like "client_5".
    For studio users, id is a UUID string.
    """
    user_id = current_user.id
    client_id = None
    
    if user_id.startswith("client_"):
        # This is a client using new auth
        client_id = int(user_id.replace("client_", ""))
        user_id = None
    
    return user_id, client_id


@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    type: Optional[str] = None,
    unread: Optional[bool] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get notifications for the current user.
    
    Query params:
    - type: Filter by notification type ('comment', 'order', 'payment', 'system')
    - unread: If true, only return unread notifications
    - limit: Max notifications to return (default 50)
    """
    user_id, client_id = _get_user_and_client_ids(current_user)
    
    notifications = NotificationService.get_notifications(
        db=db,
        user_id=user_id,
        client_id=client_id,
        type_filter=type,
        unread_only=unread or False,
        limit=limit,
    )
    
    unread_count = NotificationService.get_unread_count(
        db=db,
        user_id=user_id,
        client_id=client_id,
    )
    
    return NotificationListResponse(
        notifications=[
            NotificationResponse(
                id=n.id,
                type=n.type,
                text=n.text,
                context=n.context,
                timestamp=n.timestamp,
                is_read=n.is_read,
                avatar_url=n.avatar_url,
                # New unified fields
                category=n.category,
                event_type=n.event_type,
                title=n.title,
                message=n.message,
                priority=n.priority,
                extra_data=n.extra_data,
                # Related entities
                project_id=n.project_id,
                photo_id=n.photo_id,
                comment_id=n.comment_id,
                entity_type=n.entity_type,
                entity_id=n.entity_id,
                # Actor info
                actor_name=n.actor_name,
                actor_type=n.actor_type,
                # Timestamps
                created_at=n.created_at,
                expires_at=n.expires_at,
            )
            for n in notifications
        ],
        total=len(notifications),
        unread_count=unread_count,
    )


@router.get("/count", response_model=NotificationCountResponse)
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get unread notification count (lightweight endpoint for badge)."""
    user_id, client_id = _get_user_and_client_ids(current_user)
    
    count = NotificationService.get_unread_count(
        db=db,
        user_id=user_id,
        client_id=client_id,
    )
    
    return NotificationCountResponse(unread_count=count)


@router.post("/{notification_id}/read", response_model=MarkReadResponse)
async def mark_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Mark a single notification as read."""
    user_id, client_id = _get_user_and_client_ids(current_user)
    
    success = NotificationService.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=user_id,
        client_id=client_id,
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return MarkReadResponse(success=True, message="Notification marked as read")


@router.post("/read-all", response_model=MarkReadResponse)
async def mark_all_read(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Mark all notifications as read."""
    user_id, client_id = _get_user_and_client_ids(current_user)
    
    count = NotificationService.mark_all_read(
        db=db,
        user_id=user_id,
        client_id=client_id,
    )
    
    return MarkReadResponse(
        success=True,
        message=f"Marked {count} notification(s) as read"
    )


@router.post("/upload", response_model=NotificationResponse)
async def create_upload_notification(
    request: UploadNotificationRequest,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Create a notification for upload completion.
    
    Called once per upload batch (not per file).
    """
    user_id, client_id = _get_user_and_client_ids(current_user)
    
    # Only studio users can create upload notifications
    if client_id is not None:
        raise HTTPException(status_code=403, detail="Clients cannot create upload notifications")
    
    notification = NotificationService.create_upload_notification(
        db=db,
        user_id=user_id,
        project_id=request.project_id,
        project_name=request.project_name,
        total_files=request.total_files,
        completed_files=request.completed_files,
        failed_files=request.failed_files,
        status=request.status,
    )
    
    if not notification:
        raise HTTPException(status_code=500, detail="Failed to create notification")
    
    return NotificationResponse(
        id=notification.id,
        type=notification.type,
        text=notification.text,
        context=notification.context,
        timestamp=notification.timestamp,
        is_read=notification.is_read,
        avatar_url=notification.avatar_url,
        category=notification.category,
        event_type=notification.event_type,
        title=notification.title,
        message=notification.message,
        priority=notification.priority,
        extra_data=notification.extra_data,
        project_id=notification.project_id,
        photo_id=notification.photo_id,
        comment_id=notification.comment_id,
        entity_type=notification.entity_type,
        entity_id=notification.entity_id,
        actor_name=notification.actor_name,
        actor_type=notification.actor_type,
        created_at=notification.created_at,
        expires_at=notification.expires_at,
    )


@router.delete("/cleanup")
async def cleanup_notifications(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Clean up expired notifications (admin only).
    
    This endpoint removes notifications that have passed their expiry date.
    """
    user_id, client_id = _get_user_and_client_ids(current_user)
    
    # Only allow for studio users (not clients)
    if client_id is not None:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    results = NotificationCleanupService.cleanup_all_categories(db)
    
    total_deleted = sum(results.values())
    
    return {
        "success": True,
        "message": f"Cleaned up {total_deleted} expired notification(s)",
        "details": results,
    }
