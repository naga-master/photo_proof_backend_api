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


class CreateStudioRequest(BaseModel):
    name: str
    email: str
    business_name: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    logo_url: Optional[str] = None
    brand_color: Optional[str] = None
    password: Optional[str] = None
    password_encoding: Optional[str] = Field(default="plain", alias="passwordEncoding")

    model_config = {
        "populate_by_name": True,
        "str_strip_whitespace": True,
    }


class StudioOnboardingRequest(CreateStudioRequest):
    owner_name: str = Field(alias="ownerName")
    password: str
    password_confirm: str = Field(alias="passwordConfirm")
    password_encoding: Optional[str] = Field(default="plain", alias="passwordEncoding")

    model_config = {
        "populate_by_name": True,
        "str_strip_whitespace": True,
    }


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
    replace_image_id: Optional[str] = Field(default=None, alias="replaceImageId")
    version_name: Optional[str] = Field(default=None, alias="versionName")

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
    replace_image_id: Optional[str] = Field(default=None, alias="replaceImageId")
    version_name: Optional[str] = Field(default=None, alias="versionName")
    checksum: Optional[str] = None
    force_replace: bool = Field(default=False, alias="forceReplace")

    model_config = {
        "populate_by_name": True,
        "str_strip_whitespace": True,
    }
