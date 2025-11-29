"""
Photo Repository

Handles data access operations for Photo entities.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from .base import BaseRepository
from app.db.models.photo import Photo


class PhotoRepository(BaseRepository[Photo]):
    """Repository for Photo entity operations."""
    
    def __init__(self, db: Session):
        super().__init__(Photo, db)
    
    def get_by_project(
        self, 
        project_id: int, 
        skip: int = 0, 
        limit: int = 100,
        folder_id: Optional[int] = None
    ) -> List[Photo]:
        """Get photos for a specific project."""
        query = select(Photo).where(Photo.project_id == project_id)
        
        if folder_id is not None:
            query = query.where(Photo.folder_id == folder_id)
        else:
            # If no folder specified, get root-level photos (no folder)
            query = query.where(Photo.folder_id.is_(None))
        
        query = query.order_by(Photo.position, Photo.created_at)
        query = query.offset(skip).limit(limit)
        
        result = self.db.execute(query)
        return list(result.scalars().all())
    
    def get_all_by_project(self, project_id: int) -> List[Photo]:
        """Get all photos for a project (including in folders)."""
        query = (
            select(Photo)
            .where(Photo.project_id == project_id)
            .order_by(Photo.folder_id, Photo.position, Photo.created_at)
        )
        result = self.db.execute(query)
        return list(result.scalars().all())
    
    def count_by_project(self, project_id: int) -> int:
        """Count photos in a project."""
        query = (
            select(func.count(Photo.id))
            .where(Photo.project_id == project_id)
        )
        result = self.db.execute(query)
        return result.scalar() or 0
    
    def get_favorites(self, project_id: int, user_id: str) -> List[Photo]:
        """Get favorited photos for a user in a project."""
        from app.db.models.photo import UserPhotoFavorite
        
        query = (
            select(Photo)
            .join(UserPhotoFavorite, Photo.id == UserPhotoFavorite.photo_id)
            .where(
                UserPhotoFavorite.project_id == project_id,
                UserPhotoFavorite.user_id == user_id
            )
            .order_by(UserPhotoFavorite.created_at.desc())
        )
        result = self.db.execute(query)
        return list(result.scalars().all())
    
    def get_selections(self, project_id: int, user_id: str) -> List[Photo]:
        """Get selected photos for a user in a project."""
        from app.db.models.photo import UserPhotoSelection
        
        query = (
            select(Photo)
            .join(UserPhotoSelection, Photo.id == UserPhotoSelection.photo_id)
            .where(
                UserPhotoSelection.project_id == project_id,
                UserPhotoSelection.user_id == user_id
            )
            .order_by(UserPhotoSelection.created_at.desc())
        )
        result = self.db.execute(query)
        return list(result.scalars().all())
    
    def update_position(self, photo_id: int, position: int) -> Optional[Photo]:
        """Update photo position for ordering."""
        return self.update(photo_id, {'position': position})
    
    def move_to_folder(self, photo_id: int, folder_id: Optional[int]) -> Optional[Photo]:
        """Move photo to a folder (or root if folder_id is None)."""
        return self.update(photo_id, {'folder_id': folder_id})
    
    def bulk_move_to_folder(
        self, 
        photo_ids: List[int], 
        folder_id: Optional[int]
    ) -> int:
        """Move multiple photos to a folder. Returns count of updated photos."""
        from sqlalchemy import update as sql_update
        
        stmt = (
            sql_update(Photo)
            .where(Photo.id.in_(photo_ids))
            .values(folder_id=folder_id)
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount
