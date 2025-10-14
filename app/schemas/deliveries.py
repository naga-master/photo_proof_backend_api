"""Digital delivery and sharing schemas."""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict


class DeliveryMethod(str):
    """Delivery method options."""
    DOWNLOAD_LINK = "download_link"
    CLOUD_STORAGE = "cloud_storage"
    PHYSICAL_MEDIA = "physical_media"
    MOBILE_APP = "mobile_app"


class DeliveryStatus(str):
    """Delivery status tracking."""
    PREPARING = "preparing"
    READY = "ready"
    SENT = "sent"
    DOWNLOADED = "downloaded"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class DeliveryPackage(BaseModel):
    """Digital delivery package."""
    id: str
    project_id: str
    client_id: str
    name: str
    description: Optional[str] = None
    method: str
    status: str
    download_url: Optional[str] = None
    expiry_date: Optional[datetime] = None
    password_protected: bool = False
    download_limit: Optional[int] = None
    download_count: int = 0
    file_count: int
    total_size_mb: float
    created_at: datetime
    updated_at: datetime
    accessed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DeliveryFile(BaseModel):
    """Individual file in a delivery package."""
    id: str
    package_id: str
    filename: str
    original_filename: str
    file_size_mb: float
    file_type: str
    resolution: Optional[str] = None
    download_count: int = 0
    is_selected: bool = True


class CreateDeliveryRequest(BaseModel):
    """Request to create a delivery package."""
    project_id: str
    name: str
    description: Optional[str] = None
    method: str = DeliveryMethod.DOWNLOAD_LINK
    file_ids: List[str]
    expiry_days: Optional[int] = 30
    password_protected: bool = False
    download_limit: Optional[int] = None
    custom_message: Optional[str] = None


# Alias for backward compatibility
DeliveryRequest = CreateDeliveryRequest


class DownloadLink(BaseModel):
    """Download link information."""
    id: str
    package_id: str
    url: str
    expires_at: datetime
    created_at: datetime


class DeliveryTracking(BaseModel):
    """Download tracking information."""
    id: str
    link_id: str
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    downloaded_at: datetime


class DeliverySettings(BaseModel):
    """Delivery configuration settings."""
    id: str
    studio_id: str
    default_expiry_days: int = 30
    max_download_limit: int = 10
    allow_client_selection: bool = True
    watermark_enabled: bool = False
    compression_quality: int = 90
    auto_notification: bool = True
    branding_enabled: bool = True
    custom_download_page: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DeliveryAnalytics(BaseModel):
    """Delivery performance analytics."""
    total_packages: int
    active_packages: int
    total_downloads: int
    popular_formats: Dict[str, int]
    client_engagement: Dict[str, float]
    delivery_success_rate: float


class ClientDeliveryPreferences(BaseModel):
    """Client's delivery preferences."""
    id: str
    client_id: str
    preferred_method: str
    notification_email: Optional[str] = None
    auto_download: bool = False
    quality_preference: str = "high"  # 'high', 'medium', 'web'
    format_preferences: List[str] = []

    model_config = ConfigDict(from_attributes=True)