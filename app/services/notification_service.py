"""Notification service for real-time alerts and messaging."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from enum import Enum

from app.schemas.notifications import (
    Notification,
    NotificationRequest,
    NotificationTemplate,
    MessageThread,
    MessageRequest,
    NotificationPreferences,
    NotificationStatus,
    NotificationType
)


class NotificationService:
    """Service for managing notifications and messaging."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_notification(
        self, 
        studio_id: str, 
        request: NotificationRequest
    ) -> Notification:
        """Create a new notification."""
        notification = Notification(
            id=f"notif_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            studio_id=studio_id,
            user_id=request.user_id,
            type=request.type,
            title=request.title,
            message=request.message,
            data=request.data or {},
            status=NotificationStatus.UNREAD,
            priority=request.priority or "medium",
            scheduled_for=request.scheduled_for,
            expires_at=request.expires_at,
            created_at=datetime.utcnow()
        )
        
        return notification
    
    def get_notifications(
        self, 
        user_id: str,
        status: Optional[NotificationStatus] = None,
        type: Optional[NotificationType] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get user notifications with filtering."""
        # Mock notifications
        notifications = [
            Notification(
                id="notif_001",
                studio_id="studio_001",
                user_id=user_id,
                type=NotificationType.PROJECT_UPDATE,
                title="Gallery Ready",
                message="Your wedding gallery is now ready for viewing",
                data={"project_id": "proj_001", "gallery_url": "/gallery/proj_001"},
                status=NotificationStatus.UNREAD,
                priority="high",
                created_at=datetime.utcnow() - timedelta(hours=2)
            ),
            Notification(
                id="notif_002",
                studio_id="studio_001", 
                user_id=user_id,
                type=NotificationType.PAYMENT_RECEIVED,
                title="Payment Received",
                message="Payment of $2,500 received for Invoice #INV-001",
                data={"invoice_id": "inv_001", "amount": 2500.00},
                status=NotificationStatus.READ,
                priority="medium",
                created_at=datetime.utcnow() - timedelta(days=1)
            ),
            Notification(
                id="notif_003",
                studio_id="studio_001",
                user_id=user_id,
                type=NotificationType.CLIENT_MESSAGE,
                title="New Message",
                message="Sarah Davis sent you a message about the portrait session",
                data={"client_id": "client_002", "message_id": "msg_001"},
                status=NotificationStatus.UNREAD,
                priority="medium",
                created_at=datetime.utcnow() - timedelta(hours=6)
            )
        ]
        
        # Apply filters
        if status:
            notifications = [n for n in notifications if n.status == status]
        if type:
            notifications = [n for n in notifications if n.type == type]
        
        return {
            "notifications": notifications,
            "total": len(notifications),
            "unread_count": len([n for n in notifications if n.status == NotificationStatus.UNREAD]),
            "page": page,
            "limit": limit
        }
    
    def mark_as_read(self, notification_id: str, user_id: str) -> Notification:
        """Mark notification as read."""
        # Mock implementation
        notification = Notification(
            id=notification_id,
            studio_id="studio_001",
            user_id=user_id,
            type=NotificationType.PROJECT_UPDATE,
            title="Gallery Ready",
            message="Your wedding gallery is now ready for viewing",
            status=NotificationStatus.READ,
            priority="high",
            created_at=datetime.utcnow() - timedelta(hours=2),
            read_at=datetime.utcnow()
        )
        
        return notification
    
    def mark_all_as_read(self, user_id: str) -> Dict[str, Any]:
        """Mark all notifications as read for user."""
        return {
            "user_id": user_id,
            "marked_count": 5,
            "marked_at": datetime.utcnow().isoformat()
        }
    
    def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """Delete a notification."""
        # Mock deletion
        return True
    
    def send_email_notification(
        self, 
        template_id: str, 
        recipient: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send email notification using template."""
        # Mock email sending
        return {
            "message_id": f"email_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "template_id": template_id,
            "recipient": recipient,
            "status": "sent",
            "sent_at": datetime.utcnow().isoformat(),
            "delivery_status": "delivered"
        }
    
    def create_message_thread(
        self, 
        studio_id: str, 
        client_id: str, 
        project_id: Optional[str] = None
    ) -> MessageThread:
        """Create a new message thread with client."""
        thread = MessageThread(
            id=f"thread_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            studio_id=studio_id,
            client_id=client_id,
            project_id=project_id,
            subject=f"Discussion about Project {project_id}" if project_id else "General Discussion",
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        return thread
    
    def send_message(
        self, 
        thread_id: str, 
        sender_id: str, 
        request: MessageRequest
    ) -> Dict[str, Any]:
        """Send message in thread."""
        message = {
            "id": f"msg_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "thread_id": thread_id,
            "sender_id": sender_id,
            "content": request.content,
            "attachments": request.attachments or [],
            "sent_at": datetime.utcnow().isoformat(),
            "status": "delivered"
        }
        
        return message
    
    def get_message_threads(
        self, 
        user_id: str,
        status: Optional[str] = None
    ) -> List[MessageThread]:
        """Get message threads for user."""
        # Mock threads
        threads = [
            MessageThread(
                id="thread_001",
                studio_id="studio_001",
                client_id="client_001",
                project_id="proj_001",
                subject="Wedding Photography Discussion",
                status="active",
                last_message_at=datetime.utcnow() - timedelta(hours=2),
                unread_count=2,
                created_at=datetime.utcnow() - timedelta(days=7)
            ),
            MessageThread(
                id="thread_002",
                studio_id="studio_001",
                client_id="client_002",
                project_id="proj_002",
                subject="Portrait Session Follow-up",
                status="active",
                last_message_at=datetime.utcnow() - timedelta(days=1),
                unread_count=0,
                created_at=datetime.utcnow() - timedelta(days=3)
            )
        ]
        
        if status:
            threads = [t for t in threads if t.status == status]
        
        return threads
    
    def get_notification_templates(self, studio_id: str) -> List[NotificationTemplate]:
        """Get available notification templates."""
        templates = [
            NotificationTemplate(
                id="gallery_ready",
                name="Gallery Ready",
                subject="Your photos are ready!",
                content="Hi {{client_name}}, your {{project_type}} gallery is now ready for viewing. Click here to access: {{gallery_url}}",
                type=NotificationType.PROJECT_UPDATE,
                variables=["client_name", "project_type", "gallery_url"],
                is_active=True
            ),
            NotificationTemplate(
                id="payment_reminder",
                name="Payment Reminder",
                subject="Payment Reminder - Invoice {{invoice_number}}",
                content="Hello {{client_name}}, this is a friendly reminder that your payment of ${{amount}} for Invoice {{invoice_number}} is due on {{due_date}}.",
                type=NotificationType.PAYMENT_REMINDER,
                variables=["client_name", "invoice_number", "amount", "due_date"],
                is_active=True
            ),
            NotificationTemplate(
                id="session_reminder",
                name="Session Reminder",
                subject="Upcoming Photography Session",
                content="Hi {{client_name}}, this is a reminder about your {{session_type}} session scheduled for {{session_date}} at {{session_time}}. Location: {{location}}",
                type=NotificationType.APPOINTMENT_REMINDER,
                variables=["client_name", "session_type", "session_date", "session_time", "location"],
                is_active=True
            )
        ]
        
        return templates
    
    def update_notification_preferences(
        self, 
        user_id: str, 
        preferences: NotificationPreferences
    ) -> NotificationPreferences:
        """Update user notification preferences."""
        # Mock preferences update
        updated_preferences = NotificationPreferences(
            user_id=user_id,
            email_notifications=preferences.email_notifications,
            push_notifications=preferences.push_notifications,
            sms_notifications=preferences.sms_notifications,
            notification_types=preferences.notification_types,
            quiet_hours_start=preferences.quiet_hours_start,
            quiet_hours_end=preferences.quiet_hours_end,
            updated_at=datetime.utcnow()
        )
        
        return updated_preferences
    
    def get_notification_analytics(self, studio_id: str) -> Dict[str, Any]:
        """Get notification analytics and metrics."""
        return {
            "total_sent": 1247,
            "delivery_rate": 98.5,
            "open_rate": 76.3,
            "click_rate": 23.7,
            "unsubscribe_rate": 0.8,
            "by_type": {
                "project_updates": 45.2,
                "payment_reminders": 23.1,
                "appointment_reminders": 18.7,
                "promotional": 13.0
            },
            "engagement_trends": [
                {"date": "2024-01-01", "sent": 45, "opened": 34, "clicked": 12},
                {"date": "2024-01-02", "sent": 38, "opened": 29, "clicked": 8},
                {"date": "2024-01-03", "sent": 52, "opened": 41, "clicked": 15}
            ],
            "best_sending_times": {
                "day_of_week": "Tuesday",
                "hour_of_day": 10,
                "open_rate": 82.4
            }
        }