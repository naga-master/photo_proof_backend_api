"""Enumerations shared across schemas."""

from enum import Enum


class UserRole(str, Enum):
    STUDIO = "studio"
    CLIENT = "client"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class BatchActionType(str, Enum):
    SELECT = "select"
    FAVORITE = "favorite"
    COMMENT = "comment"
    APPROVE = "approve"
    DOWNLOAD = "download"
