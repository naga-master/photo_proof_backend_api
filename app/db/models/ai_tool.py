"""AI Tool model."""

from sqlalchemy import Column, String, Boolean, Integer, Text
from .base import Base, TimestampMixin


class AITool(Base, TimestampMixin):
    """AI Tool configuration model."""
    
    __tablename__ = "ai_tools"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    thumbnail_path = Column(String(255), nullable=False)
    tool_id = Column(String(50), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)
