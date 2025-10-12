"""Request payload schemas."""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class CreateCategoryRequest(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    is_default: bool = False
    order_index: Optional[int] = None


class CreateProjectRequest(BaseModel):
    name: str
    description: Optional[str] = None
    client_id: Optional[str] = None
    client_name: str
    client_email: str
    client_phone: Optional[str] = None
    project_type: Optional[str] = None
    shoot_date: Optional[date] = None
    categories: Optional[List[CreateCategoryRequest]] = None


class CreateClientRequest(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None


class UpdateImageRequest(BaseModel):
    category_id: Optional[str] = Field(default=None, alias="categoryId")
    is_selected: Optional[bool] = Field(default=None, alias="isSelected")
    is_favorite: Optional[bool] = Field(default=None, alias="isFavorite")
    rating: Optional[int] = None
    tags: Optional[List[str]] = None

    model_config = {
        "populate_by_name": True,
        "str_strip_whitespace": True,
    }


class CreateCommentRequest(BaseModel):
    content: str
    parent_id: Optional[str] = None


class UploadFileDescriptor(BaseModel):
    file_name: str = Field(alias="fileName")
    file_size: int = Field(alias="fileSize")
    content_type: Optional[str] = Field(default=None, alias="contentType")
    category_id: Optional[str] = Field(default=None, alias="categoryId")

    model_config = {
        "populate_by_name": True,
        "str_strip_whitespace": True,
    }


class InitiateUploadRequest(BaseModel):
    project_id: str = Field(alias="projectId")
    files: List[UploadFileDescriptor]

    model_config = {
        "populate_by_name": True,
        "str_strip_whitespace": True,
    }


class CompleteUploadRequest(BaseModel):
    project_id: str = Field(alias="projectId")
    category_id: Optional[str] = Field(default=None, alias="categoryId")
    file_name: str = Field(alias="fileName")
    original_file_name: str = Field(alias="originalFileName")
    file_size: int = Field(alias="fileSize")
    content_type: Optional[str] = Field(default=None, alias="contentType")
    upload_url: Optional[str] = Field(default=None, alias="uploadUrl")

    model_config = {
        "populate_by_name": True,
        "str_strip_whitespace": True,
    }
