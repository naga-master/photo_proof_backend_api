"""Notification service for creating and managing notifications."""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.models.notification import Notification
from app.db.models.user import User, Client
from app.db.models.project import Project
from app.db.models.photo import Photo


def _format_timestamp(dt: datetime) -> str:
    """Format datetime as human-readable relative timestamp."""
    now = datetime.utcnow()
    diff = now - dt
    
    minutes = int(diff.total_seconds() / 60)
    hours = int(diff.total_seconds() / 3600)
    days = int(diff.total_seconds() / 86400)
    
    if minutes < 1:
        return "Just now"
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    if hours < 24:
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    if days < 7:
        return f"{days} day{'s' if days > 1 else ''} ago"
    return dt.strftime("%b %d, %Y")


class NotificationService:
    """Service for notification operations."""
    
    @staticmethod
    def create_comment_notification(
        db: Session,
        comment_id: int,
        comment_text: str,
        photo_id: int,
        project_id: int,
        commenter_user_id: Optional[str] = None,
        commenter_client_id: Optional[int] = None,
        commenter_name: str = "Someone",
        commenter_type: str = "client"  # 'studio' or 'client'
    ) -> List[Notification]:
        """
        Create notification(s) when a comment is posted.
        
        - If commenter is client → notify all studio users
        - If commenter is studio → notify the project's client
        """
        notifications = []
        
        # Get project to find studio_id and client_id
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return notifications
        
        # Get photo for context
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        photo_name = photo.original_filename if photo else "a photo"
        
        # Build notification content
        text = f"{commenter_name} commented on"
        context = f"{photo_name} in {project.title}"
        
        if commenter_type == "client":
            # Client commented → notify studio staff only (not other clients)
            studio_users = db.query(User).filter(
                User.studio_id == project.studio_id,
                User.role.in_(['studio_owner', 'studio_admin', 'studio_photographer', 'studio'])
            ).all()
            
            for user in studio_users:
                notification = Notification(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    client_id=None,
                    type="comment",
                    text=text,
                    context=context,
                    timestamp=_format_timestamp(datetime.utcnow()),
                    is_read=False,
                    project_id=project_id,
                    photo_id=photo_id,
                    comment_id=comment_id,
                    actor_name=commenter_name,
                    actor_type=commenter_type,
                )
                db.add(notification)
                notifications.append(notification)
        else:
            # Studio user commented → notify the project's client
            notification = Notification(
                id=str(uuid.uuid4()),
                user_id=None,
                client_id=project.client_id,
                type="comment",
                text=text,
                context=context,
                timestamp=_format_timestamp(datetime.utcnow()),
                is_read=False,
                project_id=project_id,
                photo_id=photo_id,
                comment_id=comment_id,
                actor_name=commenter_name,
                actor_type=commenter_type,
            )
            db.add(notification)
            notifications.append(notification)
        
        db.commit()
        return notifications
    
    @staticmethod
    def get_notifications(
        db: Session,
        user_id: Optional[str] = None,
        client_id: Optional[int] = None,
        type_filter: Optional[str] = None,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """Get notifications for a user or client."""
        query = db.query(Notification)
        
        # Filter by recipient
        if user_id:
            query = query.filter(Notification.user_id == user_id)
        elif client_id:
            query = query.filter(Notification.client_id == client_id)
        else:
            return []
        
        # Filter by type
        if type_filter:
            query = query.filter(Notification.type == type_filter)
        
        # Filter unread only
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        # Order by newest first
        query = query.order_by(Notification.created_at.desc())
        
        # Limit results
        query = query.limit(limit)
        
        notifications = query.all()
        
        # Update timestamps to be relative
        for n in notifications:
            n.timestamp = _format_timestamp(n.created_at)
        
        return notifications
    
    @staticmethod
    def get_unread_count(
        db: Session,
        user_id: Optional[str] = None,
        client_id: Optional[int] = None
    ) -> int:
        """Get unread notification count."""
        query = db.query(Notification).filter(Notification.is_read == False)
        
        if user_id:
            query = query.filter(Notification.user_id == user_id)
        elif client_id:
            query = query.filter(Notification.client_id == client_id)
        else:
            return 0
        
        return query.count()
    
    @staticmethod
    def mark_as_read(
        db: Session,
        notification_id: str,
        user_id: Optional[str] = None,
        client_id: Optional[int] = None
    ) -> bool:
        """Mark a single notification as read."""
        query = db.query(Notification).filter(Notification.id == notification_id)
        
        # Ensure user can only mark their own notifications
        if user_id:
            query = query.filter(Notification.user_id == user_id)
        elif client_id:
            query = query.filter(Notification.client_id == client_id)
        else:
            return False
        
        notification = query.first()
        if notification:
            notification.is_read = True
            db.commit()
            return True
        return False
    
    @staticmethod
    def mark_all_read(
        db: Session,
        user_id: Optional[str] = None,
        client_id: Optional[int] = None
    ) -> int:
        """Mark all notifications as read. Returns count of updated notifications."""
        query = db.query(Notification).filter(Notification.is_read == False)
        
        if user_id:
            query = query.filter(Notification.user_id == user_id)
        elif client_id:
            query = query.filter(Notification.client_id == client_id)
        else:
            return 0
        
        count = query.update({"is_read": True})
        db.commit()
        return count
