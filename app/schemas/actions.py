"""Batch action schemas."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.enums import BatchActionType


class BatchAction(BaseModel):
    client_action_id: str
    action_type: BatchActionType
    photo_id: Optional[str] = None
    project_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: int


class BatchActionsRequest(BaseModel):
    actions: List[BatchAction]


class BatchActionResult(BaseModel):
    clientActionId: str
    reason: str


class BatchActionsResponse(BaseModel):
    accepted: List[str]
    failed: List[BatchActionResult] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
