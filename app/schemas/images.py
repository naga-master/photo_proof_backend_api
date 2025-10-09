"""Image related schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ImageVersion(BaseModel):
    id: str
    version: str
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
    category_id: Optional[str]
    versions: List[ImageVersion]
    metadata: ImageMetadata
    tags: List[str] = Field(default_factory=list)
    is_selected: bool = False
    is_favorite: bool = False
    comment_count: int = 0
    created_at: datetime
    updated_at: datetime
