"""Gallery layout management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Import our models from the root models.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from models import (
    LayoutConfigResponse,
    UpdateLayoutRequest,
    PresetLayoutsResponse,
)

from app.db.session import get_db
from app.services.layouts_service import (
    InvalidLayoutPresetError,
    ProjectNotFoundError,
    get_project_layout as get_project_layout_service,
    list_presets,
    update_project_layout as update_project_layout_service,
)


router = APIRouter(prefix="/api/v1", tags=["gallery-layouts"])


@router.get("/layouts/presets", response_model=PresetLayoutsResponse)
async def get_preset_layouts():
    """Get all available preset gallery layouts."""
    return PresetLayoutsResponse(presets=list(list_presets()))


@router.get("/projects/{project_id}/layout", response_model=LayoutConfigResponse)
async def get_project_layout(project_id: str, db: Session = Depends(get_db)):
    """Get the current layout configuration for a project."""
    try:
        return get_project_layout_service(db, project_id)
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found") from None


@router.put("/projects/{project_id}/layout", response_model=LayoutConfigResponse)
async def update_project_layout(
    project_id: str,
    layout_request: UpdateLayoutRequest,
    db: Session = Depends(get_db),
):
    """Update the layout configuration for a project (studio users only)."""
    try:
        return update_project_layout_service(db, project_id, layout_request)
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found") from None
    except InvalidLayoutPresetError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid layout_id: {exc}") from None


@router.get("/client/{client_id}/gallery/{gallery_id}/layout", response_model=LayoutConfigResponse)
async def get_client_gallery_layout(
    client_id: str,
    gallery_id: str,
    db: Session = Depends(get_db),
):
    """Get the layout configuration for client gallery view (no auth required)."""
    try:
        # Treat gallery identifier as project for now until dedicated mapping exists
        return get_project_layout_service(db, gallery_id)
    except ProjectNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gallery not found") from None