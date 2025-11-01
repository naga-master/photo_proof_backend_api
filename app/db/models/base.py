"""Re-export base classes from parent db module."""

# Import from parent db.base
from app.db.base import Base, TimestampMixin, SoftDeleteMixin

__all__ = ["Base", "TimestampMixin", "SoftDeleteMixin"]
