"""Notification cleanup service for removing old notifications."""

from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.orm import Session
# Import Integer for the cast
from sqlalchemy import Integer

from app.db.models.notification import Notification
from app.services.notification_service import CATEGORY_CONFIG


class NotificationCleanupService:
    """Service for cleaning up old notifications."""
    
    @staticmethod
    def cleanup_expired(db: Session) -> int:
        """
        Delete notifications that have passed their expiry date.
        
        Returns:
            Number of notifications deleted
        """
        deleted = db.query(Notification).filter(
            Notification.expires_at != None,
            Notification.expires_at < datetime.utcnow()
        ).delete(synchronize_session=False)
        
        db.commit()
        return deleted
    
    @staticmethod
    def cleanup_by_category(
        db: Session,
        category: str,
        older_than_days: Optional[int] = None
    ) -> int:
        """
        Delete notifications of a specific category older than specified days.
        
        Args:
            category: Notification category ('upload', 'comment', etc.)
            older_than_days: Days to keep. If None, uses category config default.
        
        Returns:
            Number of notifications deleted
        """
        if older_than_days is None:
            config = CATEGORY_CONFIG.get(category, {'retention_days': 365})
            older_than_days = config.get('retention_days', 365)
        
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        
        deleted = db.query(Notification).filter(
            Notification.category == category,
            Notification.created_at < cutoff
        ).delete(synchronize_session=False)
        
        db.commit()
        return deleted
    
    @staticmethod
    def cleanup_all_categories(db: Session) -> Dict[str, int]:
        """
        Clean up all categories based on their configured retention periods.
        
        Returns:
            Dict with category -> deleted count
        """
        results = {}
        
        for category, config in CATEGORY_CONFIG.items():
            retention_days = config.get('retention_days', 365)
            cutoff = datetime.utcnow() - timedelta(days=retention_days)
            
            deleted = db.query(Notification).filter(
                Notification.category == category,
                Notification.created_at < cutoff
            ).delete(synchronize_session=False)
            
            if deleted > 0:
                results[category] = deleted
        
        # Also clean up any with expired_at set
        expired_deleted = db.query(Notification).filter(
            Notification.expires_at != None,
            Notification.expires_at < datetime.utcnow()
        ).delete(synchronize_session=False)
        
        if expired_deleted > 0:
            results['expired'] = expired_deleted
        
        db.commit()
        return results
    
    @staticmethod
    def get_notification_stats(db: Session) -> Dict[str, Dict]:
        """
        Get statistics about notifications for monitoring.
        
        Returns:
            Dict with stats per category
        """
        from sqlalchemy import func
        
        stats = {}
        
        # Count by category
        category_counts = db.query(
            Notification.category,
            func.count(Notification.id).label('count'),
            func.sum(
                func.cast(Notification.is_read == False, Integer)
            ).label('unread')
        ).group_by(Notification.category).all()
        
        for row in category_counts:
            category = row.category or 'unknown'
            stats[category] = {
                'total': row.count,
                'unread': row.unread or 0,
            }
        
        # Get oldest notification
        oldest = db.query(
            func.min(Notification.created_at)
        ).scalar()
        
        stats['_meta'] = {
            'oldest_notification': oldest.isoformat() if oldest else None,
            'total_notifications': sum(s.get('total', 0) for s in stats.values() if isinstance(s, dict) and 'total' in s),
        }
        
        return stats



