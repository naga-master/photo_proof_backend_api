"""
Photo Proof API - Data Models

Pydantic models that mirror the frontend TypeScript types for easy migration to DynamoDB.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class UserRole(str, Enum):
    STUDIO = "studio"
    CLIENT = "client"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class User(BaseModel):
    id: str
    name: str
    email: str
    role: UserRole
    studio_id: Optional[str] = None  # Only for studio users
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
    created_at: datetime
    updated_at: datetime


class ProjectCategory(BaseModel):
    id: str
    name: str
    display_name: str
    description: Optional[str] = None
    order: int
    is_default: bool = False


class ImageVersion(BaseModel):
    id: str
    version: str  # e.g., "v1", "v2", "final"
    url: str
    thumbnail: str
    file_name: str
    uploaded_at: datetime
    is_latest: bool
    file_size: int
    description: Optional[str] = None


class ImageMetadata(BaseModel):
    width: int
    height: int
    captured_at: Optional[datetime] = None
    camera: Optional[str] = None
    lens: Optional[str] = None


class ProjectImage(BaseModel):
    id: str
    original_file_name: str
    category_id: str
    versions: List[ImageVersion]
    metadata: ImageMetadata
    tags: List[str] = Field(default_factory=list)
    is_selected: bool = False
    is_favorite: bool = False
    comment_count: int = 0
    created_at: datetime
    updated_at: datetime


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
    client_name: str
    client_email: str
    studio_id: str
    categories: List[ProjectCategory]
    images: List[ProjectImage]
    settings: ProjectSettings
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    access_url: str  # Unique URL for client access


class Comment(BaseModel):
    id: str
    image_id: str
    project_id: str
    user_id: str
    user_name: str
    user_role: UserRole
    content: str
    parent_id: Optional[str] = None  # For replies
    created_at: datetime
    updated_at: datetime


# Request/Response models
class CreateProjectRequest(BaseModel):
    name: str
    description: Optional[str] = None
    client_name: str
    client_email: str
    categories: Optional[List[ProjectCategory]] = None


class CreateCategoryRequest(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None


class UpdateImageRequest(BaseModel):
    is_selected: Optional[bool] = None
    is_favorite: Optional[bool] = None
    tags: Optional[List[str]] = None


class CreateCommentRequest(BaseModel):
    content: str
    parent_id: Optional[str] = None


# Batch actions for offline sync
class BatchActionType(str, Enum):
    SELECT = "select"
    FAVORITE = "favorite"
    COMMENT = "comment"
    APPROVE = "approve"
    DOWNLOAD = "download"


class BatchAction(BaseModel):
    client_action_id: str  # UUID from client for idempotency
    action_type: BatchActionType
    photo_id: Optional[str] = None
    project_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: int  # Unix timestamp when action was created


class BatchActionsRequest(BaseModel):
    actions: List[BatchAction]


class BatchActionResult(BaseModel):
    client_action_id: str
    success: bool
    error: Optional[str] = None


class BatchActionsResponse(BaseModel):
    accepted: List[str]  # List of client_action_ids that were processed successfully
    failed: List[BatchActionResult] = Field(default_factory=list)  # List of failed actions with reasons
    processed_count: int
    total_count: int


# Response models
class ProjectListResponse(BaseModel):
    projects: List[Project]
    total: int


class ImageListResponse(BaseModel):
    images: List[ProjectImage]
    total: int
    category_id: str


class CommentListResponse(BaseModel):
    comments: List[Comment]
    total: int
    image_id: str
