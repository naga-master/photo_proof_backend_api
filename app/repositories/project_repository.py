"""
Project Repository

Handles data access operations for Project entities.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from .base import BaseRepository
from app.db.models.project import Project


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project entity operations."""
    
    def __init__(self, db: Session):
        super().__init__(Project, db)
    
    def get_by_studio(
        self, 
        studio_id: str, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Project]:
        """Get projects for a specific studio."""
        query = select(Project).where(Project.studio_id == studio_id)
        
        if status:
            query = query.where(Project.status == status)
        
        query = query.order_by(Project.updated_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = self.db.execute(query)
        return list(result.scalars().all())
    
    def get_by_client(
        self, 
        client_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Project]:
        """Get projects for a specific client."""
        query = (
            select(Project)
            .where(Project.client_id == client_id)
            .order_by(Project.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = self.db.execute(query)
        return list(result.scalars().all())
    
    def count_by_studio(self, studio_id: str, status: Optional[str] = None) -> int:
        """Count projects for a studio."""
        query = (
            select(func.count(Project.id))
            .where(Project.studio_id == studio_id)
        )
        if status:
            query = query.where(Project.status == status)
        
        result = self.db.execute(query)
        return result.scalar() or 0
    
    def count_by_client(self, client_id: int) -> int:
        """Count projects for a client."""
        query = (
            select(func.count(Project.id))
            .where(Project.client_id == client_id)
        )
        result = self.db.execute(query)
        return result.scalar() or 0
    
    def get_with_photo_count(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get project with photo count."""
        from app.db.models.photo import Photo
        
        project = self.get_by_id(project_id)
        if not project:
            return None
        
        photo_count_query = (
            select(func.count(Photo.id))
            .where(Photo.project_id == project_id)
        )
        photo_count = self.db.execute(photo_count_query).scalar() or 0
        
        return {
            'project': project,
            'photo_count': photo_count,
        }
    
    def update_status(self, project_id: int, status: str) -> Optional[Project]:
        """Update project status."""
        return self.update(project_id, {'status': status})
    
    def toggle_lock(self, project_id: int) -> Optional[Project]:
        """Toggle project lock status."""
        project = self.get_by_id(project_id)
        if not project:
            return None
        
        return self.update(project_id, {'is_locked': not project.is_locked})
    
    def set_cover_photo(self, project_id: int, photo_id: Optional[int]) -> Optional[Project]:
        """Set the cover photo for a project."""
        return self.update(project_id, {'cover_photo_id': photo_id})
    
    def search_by_title(
        self, 
        studio_id: str, 
        search_term: str, 
        limit: int = 20
    ) -> List[Project]:
        """Search projects by title."""
        query = (
            select(Project)
            .where(
                Project.studio_id == studio_id,
                Project.title.ilike(f'%{search_term}%')
            )
            .order_by(Project.updated_at.desc())
            .limit(limit)
        )
        result = self.db.execute(query)
        return list(result.scalars().all())
