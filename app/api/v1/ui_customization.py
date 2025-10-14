"""UI customization API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.ui_customization import (
    UICustomization,
    CreateUICustomizationRequest,
    UpdateUICustomizationRequest,
    BrandingSettings,
    NavigationCustomization,
    UIPreviewRequest,
)
from app.schemas.users import UserRead
from app.services.ui_customization_service import UICustomizationService


router = APIRouter(prefix="/api/v1/ui-customization", tags=["ui-customization"])


@router.get("/themes", response_model=List[UICustomization])
async def get_ui_themes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get UI customization themes for the studio."""
    service = UICustomizationService(db)
    return await service.get_studio_themes(
        current_user.studio_id, skip, limit
    )


@router.get("/themes/active", response_model=UICustomization)
async def get_active_theme(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get the currently active UI theme."""
    service = UICustomizationService(db)
    theme = await service.get_active_theme(current_user.studio_id, current_user.id)
    
    if not theme:
        # Return default theme if none set
        theme = await service.get_default_theme()
    
    return theme


@router.post("/themes", response_model=UICustomization)
async def create_ui_theme(
    request: CreateUICustomizationRequest,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Create a new UI customization theme."""
    service = UICustomizationService(db)
    return await service.create_theme(
        current_user.studio_id, current_user.id, request
    )


@router.get("/themes/{theme_id}", response_model=UICustomization)
async def get_ui_theme(
    theme_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get a specific UI theme."""
    service = UICustomizationService(db)
    theme = await service.get_theme(theme_id)
    
    if not theme or theme.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=404,
            detail="Theme not found"
        )
    
    return theme


@router.put("/themes/{theme_id}", response_model=UICustomization)
async def update_ui_theme(
    theme_id: str,
    request: UpdateUICustomizationRequest,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Update a UI theme."""
    service = UICustomizationService(db)
    theme = await service.get_theme(theme_id)
    
    if not theme or theme.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=404,
            detail="Theme not found"
        )
    
    return await service.update_theme(theme_id, request)


@router.delete("/themes/{theme_id}")
async def delete_ui_theme(
    theme_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Delete a UI theme."""
    service = UICustomizationService(db)
    theme = await service.get_theme(theme_id)
    
    if not theme or theme.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=404,
            detail="Theme not found"
        )
    
    if theme.is_default:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete default theme"
        )
    
    await service.delete_theme(theme_id)
    return {"message": "Theme deleted successfully"}


@router.put("/themes/{theme_id}/activate")
async def activate_ui_theme(
    theme_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Activate a UI theme for the current user."""
    service = UICustomizationService(db)
    theme = await service.get_theme(theme_id)
    
    if not theme or theme.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=404,
            detail="Theme not found"
        )
    
    await service.activate_theme(current_user.id, theme_id)
    return {"message": "Theme activated successfully"}


@router.get("/branding", response_model=BrandingSettings)
async def get_branding_settings(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get branding settings for the studio."""
    service = UICustomizationService(db)
    return await service.get_branding_settings(current_user.studio_id)


@router.put("/branding", response_model=BrandingSettings)
async def update_branding_settings(
    settings: dict,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Update branding settings for the studio."""
    service = UICustomizationService(db)
    return await service.update_branding_settings(current_user.studio_id, settings)


@router.get("/navigation", response_model=NavigationCustomization)
async def get_navigation_settings(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get navigation customization for the current user."""
    service = UICustomizationService(db)
    return await service.get_navigation_settings(current_user.id)


@router.put("/navigation", response_model=NavigationCustomization)
async def update_navigation_settings(
    settings: dict,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Update navigation customization for the current user."""
    service = UICustomizationService(db)
    return await service.update_navigation_settings(current_user.id, settings)


@router.post("/preview")
async def generate_preview(
    request: UIPreviewRequest,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Generate a preview of a UI theme."""
    service = UICustomizationService(db)
    theme = await service.get_theme(request.customization_id)
    
    if not theme or theme.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=404,
            detail="Theme not found"
        )
    
    preview_url = await service.generate_preview(request)
    return {"preview_url": preview_url}


@router.get("/presets")
async def get_theme_presets(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get available theme presets."""
    service = UICustomizationService(db)
    return await service.get_theme_presets()


@router.post("/presets/{preset_name}/apply")
async def apply_theme_preset(
    preset_name: str,
    theme_name: str = Query(...),
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Apply a theme preset to create a new theme."""
    service = UICustomizationService(db)
    
    preset_config = await service.get_preset_config(preset_name)
    if not preset_config:
        raise HTTPException(
            status_code=404,
            detail="Theme preset not found"
        )
    
    request = CreateUICustomizationRequest(
        name=theme_name,
        theme_preset=preset_name,
        custom_colors=preset_config.get("colors", {}),
        layout_settings=preset_config.get("layout", {}),
        typography_settings=preset_config.get("typography", {}),
        effects_settings=preset_config.get("effects", {}),
    )
    
    theme = await service.create_theme(current_user.studio_id, current_user.id, request)
    return {"message": "Theme preset applied", "theme_id": theme.id}


@router.post("/upload-logo")
async def upload_studio_logo(
    # This would typically handle file upload
    # For now, returning a placeholder
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Upload studio logo for branding."""
    # Implementation would handle file upload to storage
    # and update branding settings with the new logo URL
    return {"message": "Logo upload endpoint - implementation needed"}


@router.post("/upload-favicon")
async def upload_studio_favicon(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Upload studio favicon for branding."""
    # Implementation would handle file upload to storage
    # and update branding settings with the new favicon URL
    return {"message": "Favicon upload endpoint - implementation needed"}