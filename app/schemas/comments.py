"""Comment schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CommentRead(BaseModel):
    id: str
    image_id: str
    user_id: str
    parent_id: Optional[str] = None
    content: str
    resolved: bool
    created_at: datetime
    updated_at: datetime
    user_name: Optional[str] = None
    user_role: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
