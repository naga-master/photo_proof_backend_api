"""User and studio related schemas."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.schemas.enums import UserRole


class User(BaseModel):
    id: str
    name: str
    email: str
    role: UserRole
    studio_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class Studio(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    owner_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
