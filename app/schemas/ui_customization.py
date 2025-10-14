"""UI customization and theming schemas."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ThemePreset(str):
    """Available theme presets."""
    MODERN_GLASS = "modern_glass"
    MINIMAL_CLEAN = "minimal_clean"
    VIBRANT_GRADIENT = "vibrant_gradient"
    DARK_PRO = "dark_pro"
    CUSTOM = "custom"


class UICustomization(BaseModel):
    """UI customization settings."""
    id: str
    studio_id: str
    user_id: Optional[str] = None  # Null for studio-wide settings
    name: str
    theme_preset: str
    custom_colors: Dict[str, str]
    layout_settings: Dict[str, Any]
    typography_settings: Dict[str, Any]
    effects_settings: Dict[str, Any]
    is_active: bool = True
    is_default: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UITheme(BaseModel):
    """UI theme configuration."""
    id: str
    studio_id: str
    name: str
    primary_color: str = "#1f2937"
    secondary_color: str = "#f3f4f6"
    accent_color: str = "#3b82f6"
    background_color: str = "#ffffff"
    text_color: str = "#111827"
    font_family: str = "Inter"
    custom_css: Optional[str] = None
    is_active: bool = True
    created_at: datetime


class CustomizationSettings(BaseModel):
    """General customization settings."""
    studio_id: str
    layout_preferences: Dict[str, Any]
    notification_settings: Dict[str, Any] 
    accessibility_options: Dict[str, Any]
    updated_at: datetime


class ThemeRequest(BaseModel):
    """Request to update theme."""
    name: str
    primary_color: str
    secondary_color: str
    accent_color: str
    background_color: str
    text_color: str
    font_family: str
    custom_css: Optional[str] = None


class CreateUICustomizationRequest(BaseModel):
    """Request to create UI customization."""
    name: str
    theme_preset: str = ThemePreset.MODERN_GLASS
    custom_colors: Optional[Dict[str, str]] = None
    layout_settings: Optional[Dict[str, Any]] = None
    typography_settings: Optional[Dict[str, Any]] = None
    effects_settings: Optional[Dict[str, Any]] = None
    is_default: bool = False


class UpdateUICustomizationRequest(BaseModel):
    """Request to update UI customization."""
    name: Optional[str] = None
    theme_preset: Optional[str] = None
    custom_colors: Optional[Dict[str, str]] = None
    layout_settings: Optional[Dict[str, Any]] = None
    typography_settings: Optional[Dict[str, Any]] = None
    effects_settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class BrandingSettings(BaseModel):
    """Studio branding configuration."""
    id: str
    studio_id: str
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: str = "#000000"
    secondary_color: str = "#666666"
    accent_color: str = "#007bff"
    font_family: str = "Inter"
    custom_css: Optional[str] = None
    watermark_enabled: bool = False
    watermark_opacity: float = 0.5
    footer_text: Optional[str] = None
    custom_domain: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class NavigationCustomization(BaseModel):
    """Navigation layout customization."""
    id: str
    user_id: str
    sidebar_collapsed: bool = False
    favorite_sections: List[str] = []
    hidden_sections: List[str] = []
    quick_actions: List[str] = []
    custom_shortcuts: Dict[str, str] = {}
    recent_items_count: int = 5

    model_config = ConfigDict(from_attributes=True)


class DevicePreview(BaseModel):
    """Device preview settings."""
    device_type: str  # 'desktop', 'tablet', 'mobile'
    width: int
    height: int
    scale: float = 1.0


class UIPreviewRequest(BaseModel):
    """Request for UI preview generation."""
    customization_id: str
    device: DevicePreview
    page_type: str = "gallery"  # 'gallery', 'dashboard', 'invoice'