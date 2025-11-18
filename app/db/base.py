"""Declarative base for SQLAlchemy models."""

from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class SoftDeleteMixin:
    """Mixin to add soft delete functionality."""

    is_deleted = Column(DateTime, nullable=True, default=None)

    def soft_delete(self):
        """Mark the record as deleted."""
        self.is_deleted = datetime.utcnow()

    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = None

    @property
    def is_active(self):
        """Check if the record is active (not soft-deleted)."""
        return self.is_deleted is None
