"""Shared utilities for gallery layout persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, List

from sqlalchemy.orm import Session

from app.db import models as db_models

from models import (
    LayoutColorTheme,
    LayoutConfigResponse,
    LayoutGridPattern,
    LayoutHeaderStyle,
    PresetLayout,
    UpdateLayoutRequest,
)


class ProjectNotFoundError(Exception):
    """Raised when a project cannot be located."""


class InvalidLayoutPresetError(Exception):
    """Raised when attempting to apply an unknown layout preset."""


PRESET_LAYOUTS: List[PresetLayout] = [
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


DEFAULT_LAYOUT_ID = "layout-001"


def list_presets() -> Iterable[PresetLayout]:
    """Return all available layout presets."""

    return PRESET_LAYOUTS


def _default_layout_response() -> LayoutConfigResponse:
    preset = get_preset(DEFAULT_LAYOUT_ID) or PRESET_LAYOUTS[0]
    return LayoutConfigResponse(
        layout_id=preset.id,
        header_style=preset.header_style,
        grid_pattern=preset.grid_pattern,
        color_theme=preset.color_theme,
        cover_image_url=None,
        custom_config=None,
    )


def get_preset(layout_id: str) -> PresetLayout | None:
    """Find a preset by identifier."""

    return next((preset for preset in PRESET_LAYOUTS if preset.id == layout_id), None)


def _build_response(record: db_models.ProjectLayout | None) -> LayoutConfigResponse:
    if record is None:
        return _default_layout_response()

    cover_url = None
    if record.cover_image:
        candidate = record.cover_image.s3_key_preview or record.cover_image.s3_key_original
        if candidate:
            cover_url = f"/uploads/{candidate}"

    return LayoutConfigResponse(
        layout_id=record.layout_id,
        header_style=LayoutHeaderStyle(record.header_style),
        grid_pattern=LayoutGridPattern(record.grid_pattern),
        color_theme=LayoutColorTheme(record.color_theme),
        cover_image_url=cover_url,
        custom_config=record.custom_config,
    )


def get_project_layout(db: Session, project_id: str) -> LayoutConfigResponse:
    """Retrieve the persisted layout configuration for a project."""

    project = (
        db.query(db_models.Project)
        .filter(db_models.Project.id == project_id)
        .first()
    )
    if not project:
        raise ProjectNotFoundError(project_id)

    return _build_response(project.layout)


def update_project_layout(db: Session, project_id: str, payload: UpdateLayoutRequest) -> LayoutConfigResponse:
    """Persist a layout selection for the given project."""

    project = (
        db.query(db_models.Project)
        .filter(db_models.Project.id == project_id)
        .first()
    )
    if not project:
        raise ProjectNotFoundError(project_id)

    preset = get_preset(payload.layout_id)
    if not preset:
        raise InvalidLayoutPresetError(payload.layout_id)

    layout = project.layout or db_models.ProjectLayout(project_id=project_id, created_at=datetime.utcnow())

    header = (payload.header_style or preset.header_style).value
    grid = (payload.grid_pattern or preset.grid_pattern).value
    color = (payload.color_theme or preset.color_theme).value

    layout.layout_id = payload.layout_id
    layout.header_style = header
    layout.grid_pattern = grid
    layout.color_theme = color
    layout.cover_image_id = payload.cover_image_id
    layout.custom_config = payload.custom_config.model_dump() if payload.custom_config else None
    layout.updated_at = datetime.utcnow()

    project.layout = layout
    project.updated_at = datetime.utcnow()

    db.add(project)
    db.commit()
    db.refresh(layout)

    return _build_response(layout)
