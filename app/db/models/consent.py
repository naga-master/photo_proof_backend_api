"""Consent management models for DPDPA 2023 compliance."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


def _uuid() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())


class UserConsent(Base):
    """User consent records for DPDPA compliance."""
    __tablename__ = "user_consents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Consent details
    consent_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'essential', 'marketing_emails', 'sms_notifications', 'analytics'
    consent_given: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consent_version: Mapped[str] = mapped_column(String(10), default="1.0")
    
    # Timestamps
    consent_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    withdrawal_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Audit trail
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Additional metadata
    consent_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="consents")


class DataExportRequest(Base):
    """Data export requests for DPDPA Right to Data Portability."""
    __tablename__ = "data_export_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Request details
    export_format: Mapped[str] = mapped_column(String(10), default="json")  # 'json', 'csv'
    include_contracts: Mapped[bool] = mapped_column(Boolean, default=True)
    include_signatures: Mapped[bool] = mapped_column(Boolean, default=True)
    include_activity_logs: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # 'pending', 'completed', 'failed', 'expired'
    
    # File details
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    download_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    downloaded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Audit
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="data_exports")


class AccountDeletionRequest(Base):
    """Account deletion requests for DPDPA Right to Erasure."""
    __tablename__ = "account_deletion_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Request details
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    confirmation: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # 'pending', 'approved', 'rejected', 'completed'
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Retention check
    active_contracts_count: Mapped[int] = mapped_column(Integer, default=0)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False)
    deletion_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Audit
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="deletion_requests")
