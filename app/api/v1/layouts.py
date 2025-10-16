"""Gallery layout management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_studio_user
from app.db.session import get_db
from app.schemas import UserRead
from app.services.layouts_service import (
    InvalidLayoutPresetError,
    ProjectNotFoundError,
    get_project_layout as service_get_project_layout,
    list_presets,
    update_project_layout as service_update_project_layout,
)

# Import our models from the root models.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from models import (
    LayoutConfigResponse,
    UpdateLayoutRequest,
    PresetLayoutsResponse,
)


router = APIRouter(prefix="/api/v1/layouts", tags=["gallery-layouts"])


@router.get("/presets", response_model=PresetLayoutsResponse)
async def get_preset_layouts():
    """Get all available preset layouts."""
    return PresetLayoutsResponse(presets=list(list_presets()))


@router.get("/project/{project_id}/layout", response_model=LayoutConfigResponse)
async def get_project_layout(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get the layout configuration for a specific project."""
    try:
        return service_get_project_layout(db, project_id)
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found") from None


@router.put("/project/{project_id}/layout", response_model=LayoutConfigResponse)
async def update_project_layout(
    project_id: str,
    layout_config: UpdateLayoutRequest,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_studio_user),
):
    """Update the layout configuration for a project."""
    try:
        return service_update_project_layout(db, project_id, layout_config)
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found") from None
    except InvalidLayoutPresetError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid layout_id: {exc}") from None