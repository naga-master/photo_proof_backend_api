"""AI Tools service for managing AI tool configurations."""

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models import AITool
from app.schemas.ai_tools import AIToolCreate, AIToolUpdate, AIToolResponse


class AIToolsService:
    """Service for managing AI tools."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_tools(self, active_only: bool = True) -> List[AITool]:
        """Get all AI tools, optionally filtered by active status."""
        query = select(AITool)
        if active_only:
            query = query.where(AITool.is_active == True)
        query = query.order_by(AITool.order_index)
        
        result = self.db.execute(query)
        return list(result.scalars().all())
    
    def get_tool_by_id(self, tool_id: str) -> AITool | None:
        """Get AI tool by ID."""
        query = select(AITool).where(AITool.id == tool_id)
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    def get_tool_by_tool_id(self, tool_id: str) -> AITool | None:
        """Get AI tool by tool_id (e.g., 'photoBooth')."""
        query = select(AITool).where(AITool.tool_id == tool_id)
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    def create_tool(self, tool_data: AIToolCreate) -> AITool:
        """Create a new AI tool."""
        tool = AITool(
            name=tool_data.name,
            description=tool_data.description,
            thumbnail_path=tool_data.thumbnail_path,
            tool_id=tool_data.tool_id,
            is_active=tool_data.is_active,
            order_index=tool_data.order_index
        )
        
        self.db.add(tool)
        self.db.commit()
        self.db.refresh(tool)
        
        return tool
    
    def update_tool(self, tool_id: str, tool_data: AIToolUpdate) -> AITool | None:
        """Update an existing AI tool."""
        tool = self.get_tool_by_id(tool_id)
        if not tool:
            return None
        
        update_data = tool_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tool, field, value)
        
        self.db.commit()
        self.db.refresh(tool)
        
        return tool
    
    def delete_tool(self, tool_id: str) -> bool:
        """Delete an AI tool."""
        tool = self.get_tool_by_id(tool_id)
        if not tool:
            return False
        
        self.db.delete(tool)
        self.db.commit()
        
        return True
