"""Database models package."""

from .base import Base, TimestampMixin, SoftDeleteMixin
from .user import Studio, User, Client
from .project import Project, Folder
from .photo import Photo, Comment, UserPhotoFavorite, UserPhotoSelection
from .service import ServicePackage, Invoice
from .package_type import PackageType
from .store import Product, ProductOption, CartItem, Order
from .notification import Notification
from .upload import UploadSession, UploadToken
from .settings import LayoutTemplate, CommunicationSettings
from .ai_tool import AITool
from .multi_tenant import (
    StudioDomain,
    SubscriptionPlan,
    StudioSubscription,
    StudioFeature,
    StudioUsageStats,
)
from .contract import (
    Contract,
    ContractTemplate,
    ContractActivity,
    ContractEmailTemplate,
)
from .consent import (
    UserConsent,
    DataExportRequest,
    AccountDeletionRequest,
)

# Backwards compatibility aliases
Image = Photo  # Old code uses 'Image', we use 'Photo'

__all__ = [
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",
    "Studio",
    "User",
    "Client",
    "Project",
    "Folder",
    "Photo",
    "Image",  # Alias for backwards compatibility
    "Comment",
    "UserPhotoFavorite",
    "UserPhotoSelection",
    "ServicePackage",
    "Invoice",
    "PackageType",
    "Product",
    "ProductOption",
    "CartItem",
    "Order",
    "Notification",
    "UploadSession",
    "UploadToken",
    "LayoutTemplate",
    "CommunicationSettings",
    "AITool",
    # Multi-tenant models
    "StudioDomain",
    "SubscriptionPlan",
    "StudioSubscription",
    "StudioFeature",
    "StudioUsageStats",
    # Contract models
    "Contract",
    "ContractTemplate",
    "ContractActivity",
    "ContractEmailTemplate",
    # Consent models
    "UserConsent",
    "DataExportRequest",
    "AccountDeletionRequest",
]
