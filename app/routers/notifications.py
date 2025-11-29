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
)
from app.services.notification_service import NotificationService


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
                project_id=n.project_id,
                photo_id=n.photo_id,
                comment_id=n.comment_id,
                actor_name=n.actor_name,
                actor_type=n.actor_type,
                created_at=n.created_at,
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
