"""AI Tools schemas."""

from pydantic import BaseModel, ConfigDict
from datetime import datetime


class AIToolBase(BaseModel):
    """Base AI tool fields."""
    name: str
    description: str
    thumbnail_path: str
    tool_id: str


class AIToolCreate(AIToolBase):
    """AI tool creation schema."""
    is_active: bool = True
    order_index: int = 0


class AIToolUpdate(BaseModel):
    """AI tool update schema."""
    name: str | None = None
    description: str | None = None
    thumbnail_path: str | None = None
    is_active: bool | None = None
    order_index: int | None = None


class AIToolResponse(AIToolBase):
    """AI tool response schema."""
    id: str
    is_active: bool
    order_index: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AIToolListResponse(BaseModel):
    """List of AI tools response."""
    tools: list[AIToolResponse]
    total: int
