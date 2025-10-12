"""Project related schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import ProjectStatus
from app.schemas.images import ImageRead
from app.schemas.users import ClientRead


class ProjectCategoryRead(BaseModel):
    id: str
    project_id: str
    name: str
    display_name: str
    description: Optional[str] = None
    order_index: int
    is_default: bool = False
    image_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectSettingsRead(BaseModel):
    id: str
    is_password_protected: bool
    allow_downloads: bool
    allow_comments: bool
    allow_selections: bool
    allow_favorites: bool
    watermark_enabled: bool
    watermark_text: Optional[str] = None
    max_selections: Optional[int] = None
    expires_at: Optional[datetime] = None
    auto_archive_days: int
    notification_email: Optional[str] = None
    custom_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectSummary(BaseModel):
    id: str
    studio_id: str
    client_id: str
    name: str
    description: Optional[str] = None
    project_type: Optional[str] = None
    shoot_date: Optional[date] = None
    status: ProjectStatus
    total_images: int
    selected_images: int
    total_comments: int
    storage_used_bytes: int
    access_url: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectDetail(ProjectSummary):
    delivery_date: Optional[date] = None
    location: Optional[str] = None
    view_count: int = 0
    last_viewed_at: Optional[datetime] = None
    client: Optional[ClientRead] = None
    settings: Optional[ProjectSettingsRead] = None
    categories: List[ProjectCategoryRead] = Field(default_factory=list)
    images: List[ImageRead] = Field(default_factory=list)
