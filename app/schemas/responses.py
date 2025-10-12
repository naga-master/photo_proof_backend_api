"""Response payload schemas."""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.comments import CommentRead
from app.schemas.images import ImageRead
from app.schemas.projects import ProjectDetail, ProjectSummary


class ProjectListResponse(BaseModel):
    projects: List[ProjectSummary]
    total: int


class ImageListResponse(BaseModel):
    images: List[ImageRead]
    total: int
    category_id: Optional[str] = None


class CommentListResponse(BaseModel):
    comments: List[CommentRead]
    total: int
    image_id: str


class UploadUrlInfo(BaseModel):
    file_name: str = Field(alias="fileName")
    target_url: str = Field(alias="targetUrl")
    upload_id: str = Field(alias="uploadId")
    category_id: Optional[str] = Field(default=None, alias="categoryId")

    model_config = {
        "populate_by_name": True,
        "str_strip_whitespace": True,
    }


class UploadInitiateResponse(BaseModel):
    upload_urls: List[UploadUrlInfo] = Field(alias="uploadUrls")

    model_config = {
        "populate_by_name": True,
    }


class CompleteUploadResponse(BaseModel):
    image: ImageRead
    already_exists: bool = Field(default=False, alias="alreadyExists")

    model_config = {
        "populate_by_name": True,
    }
