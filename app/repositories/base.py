"""
Base Repository

Abstract base class providing common CRUD operations for all repositories.
"""

from typing import Generic, TypeVar, Optional, List, Type, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Base repository providing common database operations.
    
    Usage:
        class PhotoRepository(BaseRepository[Photo]):
            def __init__(self, db: Session):
                super().__init__(Photo, db)
    """
    
    def __init__(self, model: Type[T], db: Session):
        self.model = model
        self.db = db
    
    def get_by_id(self, id: Any) -> Optional[T]:
        """Get a single entity by ID."""
        return self.db.get(self.model, id)
    
    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Get all entities with optional pagination and filtering."""
        query = select(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        query = query.offset(skip).limit(limit)
        result = self.db.execute(query)
        return list(result.scalars().all())
    
    def create(self, obj_data: Dict[str, Any]) -> T:
        """Create a new entity."""
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def update(self, id: Any, obj_data: Dict[str, Any]) -> Optional[T]:
        """Update an entity by ID."""
        db_obj = self.get_by_id(id)
        if db_obj is None:
            return None
        
        for key, value in obj_data.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)
        
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, id: Any) -> bool:
        """Delete an entity by ID."""
        db_obj = self.get_by_id(id)
        if db_obj is None:
            return False
        
        self.db.delete(db_obj)
        self.db.commit()
        return True
    
    def exists(self, id: Any) -> bool:
        """Check if an entity exists."""
        return self.get_by_id(id) is not None
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities with optional filtering."""
        from sqlalchemy import func
        query = select(func.count()).select_from(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        result = self.db.execute(query)
        return result.scalar() or 0
