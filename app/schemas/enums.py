"""Enumerations shared across schemas."""

from enum import Enum


class UserRole(str, Enum):
    STUDIO_OWNER = "studio_owner"
    STUDIO_ADMIN = "studio_admin"
    STUDIO_PHOTOGRAPHER = "studio_photographer"
    CLIENT = "client"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    REVIEW = "review"
    DELIVERED = "delivered"
    ARCHIVED = "archived"


class ImageStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    ARCHIVED = "archived"
    DELETED = "deleted"


class BatchActionType(str, Enum):
    SELECT = "select"
    FAVORITE = "favorite"
    COMMENT = "comment"
    APPROVE = "approve"
    DOWNLOAD = "download"


class ClientStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
