"""Layout configuration schemas."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime


class LayoutConfig(BaseModel):
    """Layout configuration for galleries."""
    id: str
    name: str
    type: str  # 'grid', 'masonry', 'slideshow', 'magazine', 'fullscreen'
    settings: Dict[str, Any]
    is_default: bool = False
    created_at: datetime
    updated_at: datetime


class LayoutTemplate(BaseModel):
    """Pre-built layout template."""
    id: str
    name: str
    category: str
    description: str
    preview_url: str
    config: Optional[Dict[str, Any]] = None
    settings_schema: Optional[Dict[str, Any]] = None
    is_premium: bool = False
    is_custom: bool = False
    is_active: bool = True
    studio_id: Optional[str] = None
    tags: List[str] = []
    created_at: datetime


class LayoutSettings(BaseModel):
    """Layout settings configuration."""
    columns: Optional[int] = None
    spacing: Optional[int] = None
    aspect_ratio: Optional[str] = None
    show_captions: Optional[bool] = None
    autoplay: Optional[bool] = None
    transition: Optional[str] = None
    show_thumbnails: Optional[bool] = None
    show_controls: Optional[bool] = None


class LayoutPreview(BaseModel):
    """Layout preview information."""
    template_id: str
    settings: Dict[str, Any]
    preview_url: str
    mobile_preview_url: Optional[str] = None
    generated_at: datetime
    expires_at: datetime


class BrandingConfig(BaseModel):
    """Studio branding configuration."""
    studio_id: str
    logo_url: Optional[str] = None
    primary_color: str = "#1f2937"
    secondary_color: str = "#f3f4f6"
    accent_color: str = "#3b82f6"
    font_family: str = "Inter"
    show_logo: bool = True
    show_studio_name: bool = True
    custom_css: Optional[str] = None
    watermark_enabled: bool = False
    watermark_position: str = "bottom-right"
    watermark_opacity: float = 0.7
    updated_at: datetime


class LayoutRequest(BaseModel):
    """Base layout request."""
    template_id: str
    settings: Dict[str, Any]


class LayoutResponse(BaseModel):
    """Layout application response."""
    project_id: str
    template_id: str
    settings: Dict[str, Any]
    preview_url: str
    applied_at: datetime
    status: str


class CustomLayoutRequest(BaseModel):
    """Custom layout creation request."""
    name: str
    description: str
    settings_schema: Dict[str, Any]


class CreateLayoutRequest(BaseModel):
    """Request to create a layout configuration."""
    name: str
    type: str
    settings: Dict[str, Any]
    is_default: bool = False


class UpdateLayoutRequest(BaseModel):
    """Request to update a layout configuration."""
    name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None


class LayoutListResponse(BaseModel):
    """Response for layout list."""
    layouts: List[LayoutConfig]
    templates: List[LayoutTemplate]
    total_count: int