"""Comment schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.enums import UserRole


class Comment(BaseModel):
    id: str
    image_id: str
    project_id: str
    user_id: str
    user_name: str
    user_role: UserRole
    content: str
    parent_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
