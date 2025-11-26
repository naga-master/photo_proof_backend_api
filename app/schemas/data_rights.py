"""Schemas for DPDPA data rights management."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


# Consent Management Schemas
class ConsentPreferences(BaseModel):
    """User consent preferences."""
    essential: bool = Field(True, description="Essential services (cannot be disabled)")
    marketing_emails: bool = Field(False, description="Receive marketing emails")
    sms_notifications: bool = Field(False, description="Receive SMS notifications")
    analytics: bool = Field(False, description="Allow usage analytics")


class ConsentCreate(BaseModel):
    """Create a new consent record."""
    consent_type: str = Field(..., description="Type of consent (essential, marketing_emails, etc.)")
    consent_given: bool = Field(..., description="Whether consent is given")
    consent_version: str = Field("1.0", description="Version of consent terms")
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    location: Optional[str] = None
    consent_metadata: Optional[Dict[str, Any]] = None


class ConsentResponse(BaseModel):
    """Consent record response."""
    id: str
    user_id: str
    consent_type: str
    consent_given: bool
    consent_version: str
    consent_timestamp: datetime
    withdrawal_timestamp: Optional[datetime] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConsentWithdraw(BaseModel):
    """Withdraw a consent."""
    consent_type: str = Field(..., description="Type of consent to withdraw")
    reason: Optional[str] = None


# Data Export Schemas
class DataExportRequest(BaseModel):
    """Request to export user data."""
    export_format: str = Field("json", description="Export format (json, csv)")
    include_contracts: bool = Field(True, description="Include contracts in export")
    include_signatures: bool = Field(True, description="Include signatures in export")
    include_activity_logs: bool = Field(True, description="Include activity logs in export")


class DataExportResponse(BaseModel):
    """Data export request response."""
    id: str
    user_id: str
    export_format: str
    status: str
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    requested_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Data Correction Schemas
class DataCorrectionRequest(BaseModel):
    """Request to correct user data."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class DataCorrectionResponse(BaseModel):
    """Data correction response."""
    success: bool
    message: str
    updated_fields: List[str]


# Account Deletion Schemas
class AccountDeletionRequest(BaseModel):
    """Request to delete user account."""
    reason: Optional[str] = None
    confirmation: bool = Field(..., description="User must confirm deletion")
    password: str = Field(..., description="User password for verification")


class AccountDeletionResponse(BaseModel):
    """Account deletion request response."""
    id: str
    user_id: str
    status: str
    can_delete: bool
    active_contracts_count: int
    rejection_reason: Optional[str] = None
    deletion_date: Optional[datetime] = None
    requested_at: datetime

    class Config:
        from_attributes = True


# Data Summary Schemas
class DataSummary(BaseModel):
    """Summary of user's data."""
    user_id: str
    user_name: str
    user_email: str
    created_at: datetime
    last_login: Optional[datetime] = None
    
    # Data counts
    contracts_count: int = 0
    signatures_count: int = 0
    projects_count: int = 0
    photos_count: int = 0
    
    # Storage
    storage_used_mb: float = 0.0
    
    # Consents
    active_consents: List[str] = []
    
    # Data rights usage
    data_exports_count: int = 0
    deletion_requests_count: int = 0


class PrivacySettingsResponse(BaseModel):
    """Complete privacy settings for user."""
    consent_preferences: ConsentPreferences
    data_summary: DataSummary
    has_pending_deletion_request: bool = False
    can_delete_account: bool = True
    active_contracts_count: int = 0
