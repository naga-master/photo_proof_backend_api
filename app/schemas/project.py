"""Project and folder schemas."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


# ============================================================================
# FOLDER SCHEMAS
# ============================================================================

class FolderBase(BaseModel):
    """Base folder fields."""
    name: str = Field(..., min_length=1, max_length=255)


class FolderCreate(FolderBase):
    """Folder creation schema."""
    project_id: int
    cover_photo_id: Optional[int] = None
    order_index: int = 0


class FolderUpdate(BaseModel):
    """Folder update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    cover_photo_id: Optional[int] = None
    order_index: Optional[int] = None


class FolderResponse(FolderBase):
    """Folder response schema."""
    id: str
    project_id: int
    cover_photo_id: Optional[int] = None
    cover_photo_src: Optional[str] = None  # Computed field
    photo_count: int
    order_index: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# PROJECT SCHEMAS
# ============================================================================

class ProjectBase(BaseModel):
    """Base project fields."""
    title: str = Field(..., min_length=1, max_length=500)
    shoot_date: Optional[date] = None
    layout: str = Field(default="layout1", pattern="^layout[1-9]$")


class ProjectCreate(ProjectBase):
    """Project creation schema."""
    client_id: int
    package_id: Optional[str] = None
    is_locked: bool = False


class ProjectUpdate(BaseModel):
    """Project update schema."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    shoot_date: Optional[date] = None
    cover_photo_id: Optional[int] = None
    is_locked: Optional[bool] = None
    layout: Optional[str] = Field(None, pattern="^layout[1-9]$")
    payment_status: Optional[str] = Field(None, pattern="^(Paid|Unpaid|Due)$")
    price: Optional[Decimal] = None
    package_id: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|active|completed|archived)$")


class ProjectResponse(ProjectBase):
    """Project response schema."""
    id: int
    studio_id: str
    client_id: int
    cover_photo_id: Optional[int] = None
    cover_photo_src: Optional[str] = None  # Computed field - from cover_photo.src
    photo_count: int
    is_locked: bool
    payment_status: Optional[str] = None
    price: Optional[Decimal] = None
    package_id: Optional[str] = None
    status: str
    has_folders: bool
    created_at: datetime
    updated_at: datetime
    
    # Optional nested data
    folders: Optional[List[FolderResponse]] = None
    
    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    """List of projects response."""
    projects: List[ProjectResponse]
    total: int
