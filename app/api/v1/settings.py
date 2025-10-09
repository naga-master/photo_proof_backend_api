"""Endpoints for managing studio and project settings."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api import deps
from app.core.dependencies import get_current_user, get_data_manager
from app.schemas import Project, ProjectSettings, Studio, User, UserRole
from app.services.data_manager import DataManager


router = APIRouter(tags=["Settings"])


@router.get("/api/settings/studio/{studio_id}")
async def get_studio_settings(studio: Studio = Depends(deps.ensure_studio_access)) -> dict:
    return {
        "studio_id": studio.id,
        "studio_name": studio.name,
        "settings": {
            "default_allow_downloads": True,
            "default_allow_comments": True,
            "watermark_enabled": False,
            "auto_backup": True,
            "notification_email": studio.email,
            "timezone": "America/New_York",
            "default_categories": [
                {"name": "candid", "display_name": "Candid"},
                {"name": "portrait", "display_name": "Portrait"},
                {"name": "traditional", "display_name": "Traditional"},
            ],
        },
    }


@router.put("/api/settings/studio/{studio_id}")
async def update_studio_settings(
    settings: dict,
    studio: Studio = Depends(deps.ensure_studio_access),
) -> dict:
    return {"message": "Settings updated successfully", "settings": settings, "studio_id": studio.id}


@router.get("/api/projects/{project_id}/settings")
async def get_project_settings(project: Project = Depends(deps.get_project)) -> ProjectSettings:
    return project.settings


@router.put("/api/projects/{project_id}/settings")
async def update_project_settings(
    settings: ProjectSettings,
    project: Project = Depends(deps.get_project),
    current_user: User = Depends(get_current_user),
    data_manager: DataManager = Depends(get_data_manager),
) -> ProjectSettings:
    if current_user.role != UserRole.STUDIO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only studio users can update project settings")

    updated_project = data_manager.update_project_settings(project.id, settings)
    if not updated_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return updated_project.settings
