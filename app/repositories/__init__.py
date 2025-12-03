"""
Repository Pattern Implementation

Provides a clean abstraction layer between business logic and data access.
Each repository handles CRUD operations for a specific entity.
"""

from .base import BaseRepository
from .photo_repository import PhotoRepository
from .project_repository import ProjectRepository

__all__ = [
    'BaseRepository',
    'PhotoRepository',
    'ProjectRepository',
]
