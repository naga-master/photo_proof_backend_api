"""User, studio, and client schemas."""

from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.enums import ClientStatus, UserRole


class UserRead(BaseModel):
    id: str
    studio_id: Optional[str] = None
    name: str
    email: str
    role: UserRole
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    last_login_at: Optional[datetime] = None
    email_verified: bool = False
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudioRead(BaseModel):
    id: str
    name: str
    business_name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    logo_url: Optional[str] = None
    brand_color: Optional[str] = None
    subscription_tier: str
    subscription_status: str
    max_projects: int
    max_storage_gb: int
    storage_used_bytes: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClientRead(BaseModel):
    id: str
    studio_id: str
    user_id: Optional[str] = None
    name: str
    email: str
    phone: Optional[str] = None
    secondary_email: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    company_name: Optional[str] = None
    notes: Optional[str] = None
    status: ClientStatus
    total_projects: int
    last_project_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
