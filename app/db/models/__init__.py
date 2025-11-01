"""Database models package."""

from .base import Base, TimestampMixin, SoftDeleteMixin
from .user import Studio, User, Client
from .project import Project, Folder
from .photo import Photo, Comment, UserPhotoFavorite, UserPhotoSelection
from .service import ServicePackage, Invoice
from .store import Product, ProductOption, CartItem, Order
from .notification import Notification
from .upload import UploadSession, UploadToken
from .settings import LayoutTemplate, CommunicationSettings

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
    "Product",
    "ProductOption",
    "CartItem",
    "Order",
    "Notification",
    "UploadSession",
    "UploadToken",
    "LayoutTemplate",
    "CommunicationSettings",
]
