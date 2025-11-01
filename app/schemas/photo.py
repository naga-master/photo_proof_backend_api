"""Photo and comment schemas."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ============================================================================
# COMMENT SCHEMAS (Nested Structure)
# ============================================================================

class CommentBase(BaseModel):
    """Base comment fields."""
    text: str = Field(..., min_length=1, max_length=1000)


class CommentCreate(CommentBase):
    """Comment creation schema."""
    photo_id: int
    parent_comment_id: Optional[int] = None
    reply_to_id: Optional[int] = None  # For WhatsApp-style reply context


class CommentUpdate(BaseModel):
    """Comment update schema."""
    text: str = Field(..., min_length=1, max_length=1000)


class CommentResponse(CommentBase):
    """Comment response schema - supports nested structure."""
    id: int
    photo_id: int
    user_id: str
    author: str  # Computed: 'Client' or 'Studio'
    parent_comment_id: Optional[int] = None
    reply_to_id: Optional[int] = None
    timestamp: Optional[str] = None  # Human-readable
    is_edited: bool
    created_at: datetime
    updated_at: datetime
    
    # User info
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    
    # Nested replies (populated in service layer)
    replies: List["CommentResponse"] = []
    
    # Reply context (if reply_to_id is set)
    reply_to_author: Optional[str] = None
    reply_to_text: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# Enable forward reference for nested structure
CommentResponse.model_rebuild()


class CommentListResponse(BaseModel):
    """List of comments (tree structure)."""
    comments: List[CommentResponse]
    total: int
    photo_id: int


# ============================================================================
# PHOTO SCHEMAS
# ============================================================================

class PhotoBase(BaseModel):
    """Base photo fields."""
    alt: str = Field(..., min_length=1, max_length=500)


class PhotoCreate(BaseModel):
    """Photo creation schema - used after presigned upload."""
    project_id: int
    folder_id: Optional[str] = None
    original_filename: str
    storage_path: str
    width: int
    height: int
    file_size: int
    mime_type: str = "image/jpeg"


class PhotoUpdate(BaseModel):
    """Photo update schema."""
    alt: Optional[str] = Field(None, min_length=1, max_length=500)
    order_index: Optional[int] = None


class PhotoResponse(PhotoBase):
    """Photo response schema."""
    id: int
    project_id: int
    folder_id: Optional[str] = None
    src: str  # URL to view photo
    original_filename: str
    width: int
    height: int
    file_size: int
    mime_type: str
    thumbnail_path: Optional[str] = None
    order_index: int
    comment_count: int
    status: str
    uploaded_by: str
    created_at: datetime
    updated_at: datetime
    
    # Optional nested data
    comments: Optional[List[CommentResponse]] = None
    
    model_config = ConfigDict(from_attributes=True)


class PhotoListResponse(BaseModel):
    """List of photos response."""
    photos: List[PhotoResponse]
    total: int


# ============================================================================
# PRESIGNED UPLOAD SCHEMAS
# ============================================================================

class PresignedUploadRequest(BaseModel):
    """Request for presigned upload URL."""
    filename: str = Field(..., min_length=1, max_length=500)
    content_type: str = Field(..., pattern="^image/(jpeg|jpg|png|gif|webp)$")
    file_size: int = Field(..., gt=0, le=10*1024*1024)  # Max 10MB
    project_id: int
    folder_id: Optional[str] = None


class PresignedUploadResponse(BaseModel):
    """Response with presigned upload URL."""
    upload_url: str
    photo_id: int
    token: str
    expires_at: datetime
    method: str = "PUT"


# ============================================================================
# FAVORITE & SELECTION SCHEMAS
# ============================================================================

class FavoriteToggleRequest(BaseModel):
    """Toggle favorite status."""
    photo_id: int


class SelectionToggleRequest(BaseModel):
    """Toggle selection status."""
    photo_id: int


class FavoriteSelectionResponse(BaseModel):
    """Response for favorite/selection toggle."""
    photo_id: int
    is_favorite: Optional[bool] = None
    is_selected: Optional[bool] = None
    user_id: str
