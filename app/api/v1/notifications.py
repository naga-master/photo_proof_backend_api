"""Notifications API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.notifications import (
    NotificationRead,
    CreateNotificationRequest,
    NotificationSettings,
    UpdateNotificationSettingsRequest,
    NotificationListResponse,
    BulkNotificationAction,
    NotificationSummary,
)
from app.schemas.users import UserRead
from app.services.notification_service import NotificationService


router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    priority: Optional[str] = Query(None),
    type_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get notifications for the current user."""
    service = NotificationService(db)
    notifications, total_count, unread_count = await service.get_user_notifications(
        current_user.id, skip, limit, unread_only, priority, type_filter
    )
    
    return NotificationListResponse(
        notifications=notifications,
        unread_count=unread_count,
        total_count=total_count,
    )


@router.get("/summary", response_model=NotificationSummary)
async def get_notification_summary(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get notification summary for dashboard."""
    service = NotificationService(db)
    return await service.get_notification_summary(current_user.id)


@router.post("/", response_model=NotificationRead)
async def create_notification(
    request: CreateNotificationRequest,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Create a new notification (admin only)."""
    # Only allow studio owners to create notifications for other users
    if current_user.role != "owner" and request.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to create notifications for other users"
        )
    
    service = NotificationService(db)
    return await service.create_notification(request)


@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Mark a notification as read."""
    service = NotificationService(db)
    notification = await service.get_notification(notification_id)
    
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )
    
    await service.mark_as_read(notification_id)
    return {"message": "Notification marked as read"}


@router.put("/{notification_id}/unread")
async def mark_notification_unread(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Mark a notification as unread."""
    service = NotificationService(db)
    notification = await service.get_notification(notification_id)
    
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )
    
    await service.mark_as_unread(notification_id)
    return {"message": "Notification marked as unread"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Delete a notification."""
    service = NotificationService(db)
    notification = await service.get_notification(notification_id)
    
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )
    
    await service.delete_notification(notification_id)
    return {"message": "Notification deleted"}


@router.post("/bulk-action")
async def bulk_notification_action(
    action: BulkNotificationAction,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Perform bulk action on notifications."""
    service = NotificationService(db)
    
    # Verify all notifications belong to current user
    for notification_id in action.notification_ids:
        notification = await service.get_notification(notification_id)
        if not notification or notification.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail=f"Not authorized to modify notification {notification_id}"
            )
    
    await service.bulk_action(action.notification_ids, action.action)
    return {"message": f"Bulk action '{action.action}' completed"}


@router.put("/read-all")
async def mark_all_read(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Mark all notifications as read for the current user."""
    service = NotificationService(db)
    await service.mark_all_read(current_user.id)
    return {"message": "All notifications marked as read"}


@router.get("/settings", response_model=NotificationSettings)
async def get_notification_settings(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get notification settings for the current user."""
    service = NotificationService(db)
    return await service.get_user_settings(current_user.id)


@router.put("/settings", response_model=NotificationSettings)
async def update_notification_settings(
    request: UpdateNotificationSettingsRequest,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Update notification settings for the current user."""
    service = NotificationService(db)
    return await service.update_user_settings(current_user.id, request)


@router.post("/test")
async def send_test_notification(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Send a test notification to verify settings."""
    service = NotificationService(db)
    
    test_request = CreateNotificationRequest(
        user_id=current_user.id,
        type="system_alert",
        title="Test Notification",
        message="This is a test notification to verify your settings.",
        priority="low",
    )
    
    notification = await service.create_notification(test_request)
    return {"message": "Test notification sent", "notification_id": notification.id}