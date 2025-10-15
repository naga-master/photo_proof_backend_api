"""Gallery layout management API endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException, status

# Import our models from the root models.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from models import (
    PresetLayout,
    LayoutConfigResponse,
    UpdateLayoutRequest,
    PresetLayoutsResponse,
    LayoutHeaderStyle,
    LayoutGridPattern,
    LayoutColorTheme,
)


router = APIRouter(prefix="/api/v1", tags=["gallery-layouts"])


# Preset Layouts Configuration
PRESET_LAYOUTS = [
    PresetLayout(
        id="layout-001",
        name="Classic Portrait",
        description="Clean, professional portrait gallery with hero cover",
        header_style=LayoutHeaderStyle.COVER,
        grid_pattern=LayoutGridPattern.MASONRY_PORTRAIT,
        color_theme=LayoutColorTheme.WHITE,
    ),
    PresetLayout(
        id="layout-002",
        name="ShootProof Inspired",
        description="Generous whitespace, light minimalistic design",
        header_style=LayoutHeaderStyle.COVER,
        grid_pattern=LayoutGridPattern.MASONRY_PORTRAIT,
        color_theme=LayoutColorTheme.GREY,
        reference_url="https://thescobeys.shootproof.com/gallery/11726124/album/8602603",
    ),
    PresetLayout(
        id="layout-003",
        name="Modern Minimal",
        description="Minimal header with portrait masonry",
        header_style=LayoutHeaderStyle.TITLE_ONLY,
        grid_pattern=LayoutGridPattern.MASONRY_PORTRAIT,
        color_theme=LayoutColorTheme.GREY,
    ),
    PresetLayout(
        id="layout-004",
        name="Landscape Showcase",
        description="Warm tones for landscape photography",
        header_style=LayoutHeaderStyle.COVER,
        grid_pattern=LayoutGridPattern.MASONRY_LANDSCAPE,
        color_theme=LayoutColorTheme.CREAM,
    ),
    PresetLayout(
        id="layout-005",
        name="Clean Landscape",
        description="Elegant minimalist landscape layout",
        header_style=LayoutHeaderStyle.TITLE_ONLY,
        grid_pattern=LayoutGridPattern.MASONRY_LANDSCAPE,
        color_theme=LayoutColorTheme.CREAM,
    ),
    PresetLayout(
        id="layout-006",
        name="Editorial Grid",
        description="Magazine-style uniform grid",
        header_style=LayoutHeaderStyle.COVER,
        grid_pattern=LayoutGridPattern.GRID,
        color_theme=LayoutColorTheme.GREY,
    ),
    PresetLayout(
        id="layout-007",
        name="Bold Grid",
        description="High contrast uniform grid",
        header_style=LayoutHeaderStyle.TITLE_ONLY,
        grid_pattern=LayoutGridPattern.GRID,
        color_theme=LayoutColorTheme.BLACK,
    ),
    PresetLayout(
        id="layout-008",
        name="Story Stack",
        description="Narrative single-column layout",
        header_style=LayoutHeaderStyle.COVER,
        grid_pattern=LayoutGridPattern.STACKED,
        color_theme=LayoutColorTheme.BLACK,
    ),
    PresetLayout(
        id="layout-009",
        name="Elegant Stack",
        description="Warm, flowing single-column display",
        header_style=LayoutHeaderStyle.TITLE_ONLY,
        grid_pattern=LayoutGridPattern.STACKED,
        color_theme=LayoutColorTheme.CREAM,
    ),
    PresetLayout(
        id="layout-010",
        name="Minimalist Pure",
        description="No header, pure photo focus",
        header_style=LayoutHeaderStyle.MINIMAL,
        grid_pattern=LayoutGridPattern.MASONRY_PORTRAIT,
        color_theme=LayoutColorTheme.WHITE,
    ),
]


@router.get("/layouts/presets", response_model=PresetLayoutsResponse)
async def get_preset_layouts():
    """Get all available preset gallery layouts."""
    return PresetLayoutsResponse(presets=PRESET_LAYOUTS)


@router.get("/projects/{project_id}/layout", response_model=LayoutConfigResponse)
async def get_project_layout(project_id: str):
    """Get the current layout configuration for a project."""
    # TODO: In real implementation, fetch from database
    # For now, return a mock response
    return LayoutConfigResponse(
        layout_id="layout-001",
        header_style=LayoutHeaderStyle.COVER,
        grid_pattern=LayoutGridPattern.MASONRY_PORTRAIT,
        color_theme=LayoutColorTheme.WHITE,
        cover_image_url=None,
        custom_config=None,
    )


@router.put("/projects/{project_id}/layout", response_model=LayoutConfigResponse)
async def update_project_layout(
    project_id: str,
    layout_request: UpdateLayoutRequest
):
    """Update the layout configuration for a project (studio users only)."""
    # TODO: Add authentication for studio users
    # TODO: In real implementation, update database
    
    # Validate that the layout_id exists in presets
    layout_preset = next((l for l in PRESET_LAYOUTS if l.id == layout_request.layout_id), None)
    if not layout_preset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid layout_id: {layout_request.layout_id}"
        )
    
    # Use preset values as defaults, override with request values
    header_style = layout_request.header_style or layout_preset.header_style
    grid_pattern = layout_request.grid_pattern or layout_preset.grid_pattern
    color_theme = layout_request.color_theme or layout_preset.color_theme
    
    return LayoutConfigResponse(
        layout_id=layout_request.layout_id,
        header_style=header_style,
        grid_pattern=grid_pattern,
        color_theme=color_theme,
        cover_image_url=None,  # TODO: Generate URL from cover_image_id
        custom_config=layout_request.custom_config,
    )


@router.get("/client/{client_id}/gallery/{gallery_id}/layout", response_model=LayoutConfigResponse)
async def get_client_gallery_layout(client_id: str, gallery_id: str):
    """Get the layout configuration for client gallery view (no auth required)."""
    # TODO: In real implementation, fetch from database using gallery_id
    # For now, return a mock response
    return LayoutConfigResponse(
        layout_id="layout-001",
        header_style=LayoutHeaderStyle.COVER,
        grid_pattern=LayoutGridPattern.MASONRY_PORTRAIT,
        color_theme=LayoutColorTheme.WHITE,
        cover_image_url=None,
        custom_config=None,
    )