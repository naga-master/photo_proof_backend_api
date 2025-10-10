"""Request payload schemas."""

from typing import List, Optional

from pydantic import BaseModel

from app.schemas.projects import ProjectCategory


class CreateProjectRequest(BaseModel):
    name: str
    description: Optional[str] = None
    client_name: str
    client_email: str
    categories: Optional[List[ProjectCategory]] = None
    project_date: Optional[str] = None  # ISO date string


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
