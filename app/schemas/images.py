"""Image related schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import ImageStatus


class ImageVersionRead(BaseModel):
    id: str
    image_id: str
    version_name: str
    s3_key: str
    file_size_bytes: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    created_by: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ImageRead(BaseModel):
    id: str
    project_id: str
    category_id: str
    original_filename: str
    original_url: str = Field(alias="s3_key_original")
    thumbnail_url: Optional[str] = Field(default=None, alias="s3_key_thumbnail")
    preview_url: Optional[str] = Field(default=None, alias="s3_key_preview")
    print_url: Optional[str] = Field(default=None, alias="s3_key_print")
    file_size_bytes: int
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    captured_at: Optional[datetime] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    focal_length: Optional[str] = None
    shutter_speed: Optional[str] = None
    rating: int
    is_favorite: bool
    is_selected: bool
    comment_count: int
    status: ImageStatus
    uploaded_at: datetime
    updated_at: datetime
    tags: List[str] = Field(default_factory=list)
    versions: List[ImageVersionRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
