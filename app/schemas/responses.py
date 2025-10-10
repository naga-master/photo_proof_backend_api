"""Response payload schemas."""

from typing import List

from pydantic import BaseModel

from app.schemas.comments import Comment
from app.schemas.images import ProjectImage
from app.schemas.projects import Project


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
