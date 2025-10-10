"""Project related schemas."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.enums import ProjectStatus
from app.schemas.images import ProjectImage


class ProjectCategory(BaseModel):
    id: str
    name: str
    display_name: str
    description: Optional[str] = None
    order: int
    is_default: bool = False


class ProjectSettings(BaseModel):
    is_password_protected: bool = False
    password: Optional[str] = None
    allow_downloads: bool = True
    allow_comments: bool = True
    expires_at: Optional[datetime] = None


class Project(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    project_date: Optional[str] = None  # ISO date string
    client_name: str
    client_email: str
    studio_id: str
    categories: List[ProjectCategory]
    images: List[ProjectImage]
    settings: ProjectSettings
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    access_url: str
