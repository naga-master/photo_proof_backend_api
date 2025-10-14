"""Layout management API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.layouts import (
    LayoutConfig,
    LayoutTemplate,
    CreateLayoutRequest,
    UpdateLayoutRequest,
    LayoutListResponse,
)
from app.schemas.users import UserRead
from app.services.layout_service import LayoutService


router = APIRouter(prefix="/api/v1/layouts", tags=["layouts"])


@router.get("/", response_model=LayoutListResponse)
async def get_layouts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get all layout configurations and templates."""
    service = LayoutService(db)
    layouts = await service.get_studio_layouts(current_user.studio_id, skip, limit)
    templates = await service.get_layout_templates()
    
    return LayoutListResponse(
        layouts=layouts,
        templates=templates,
        total_count=len(layouts),
    )


@router.post("/", response_model=LayoutConfig)
async def create_layout(
    request: CreateLayoutRequest,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Create a new layout configuration."""
    service = LayoutService(db)
    return await service.create_layout(current_user.studio_id, request)


@router.get("/{layout_id}", response_model=LayoutConfig)
async def get_layout(
    layout_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get a specific layout configuration."""
    service = LayoutService(db)
    layout = await service.get_layout(layout_id)
    
    if not layout or layout.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Layout not found"
        )
    
    return layout


@router.put("/{layout_id}", response_model=LayoutConfig)
async def update_layout(
    layout_id: str,
    request: UpdateLayoutRequest,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Update a layout configuration."""
    service = LayoutService(db)
    layout = await service.get_layout(layout_id)
    
    if not layout or layout.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Layout not found"
        )
    
    return await service.update_layout(layout_id, request)


@router.delete("/{layout_id}")
async def delete_layout(
    layout_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Delete a layout configuration."""
    service = LayoutService(db)
    layout = await service.get_layout(layout_id)
    
    if not layout or layout.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Layout not found"
        )
    
    await service.delete_layout(layout_id)
    return {"message": "Layout deleted successfully"}


@router.post("/{layout_id}/set-default")
async def set_default_layout(
    layout_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Set a layout as the default for the studio."""
    service = LayoutService(db)
    layout = await service.get_layout(layout_id)
    
    if not layout or layout.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Layout not found"
        )
    
    await service.set_default_layout(current_user.studio_id, layout_id)
    return {"message": "Default layout updated"}


@router.get("/templates/{template_id}")
async def get_layout_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get a specific layout template."""
    service = LayoutService(db)
    template = await service.get_template(template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return template


@router.post("/templates/{template_id}/apply")
async def apply_layout_template(
    template_id: str,
    name: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Apply a template to create a new layout."""
    service = LayoutService(db)
    template = await service.get_template(template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Create layout from template
    request = CreateLayoutRequest(
        name=name,
        type=template.config.get("type", "grid"),
        settings=template.config,
    )
    
    return await service.create_layout(current_user.studio_id, request)