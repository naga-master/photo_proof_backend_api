"""Endpoints for managing studio and project settings."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core.dependencies import get_current_user
from app.db import models
from app.db.session import get_db
from app.schemas import ProjectSettingsRead, StudioRead, UserRead, UserRole


router = APIRouter(tags=["Settings"])


@router.get("/api/settings/studio/{studio_id}")
def get_studio_settings(studio: StudioRead = Depends(deps.ensure_studio_access)) -> dict:
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
def update_studio_settings(settings: dict, studio: StudioRead = Depends(deps.ensure_studio_access)) -> dict:
    return {"message": "Settings updated successfully", "settings": settings, "studio_id": studio.id}


@router.get("/api/projects/{project_id}/settings", response_model=ProjectSettingsRead)
def get_project_settings(project: models.Project = Depends(deps.get_project)) -> ProjectSettingsRead:
    if not project.settings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project settings not found")
    return ProjectSettingsRead.model_validate(project.settings)


@router.put("/api/projects/{project_id}/settings", response_model=ProjectSettingsRead)
def update_project_settings(
    settings: ProjectSettingsRead,
    project: models.Project = Depends(deps.get_project),
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectSettingsRead:
    if current_user.role == UserRole.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only studio users can update project settings")

    project_settings = project.settings
    if not project_settings:
        project_settings = models.ProjectSettings(project_id=project.id)
        db.add(project_settings)

    for key, value in settings.model_dump(exclude={"id", "created_at", "updated_at"}).items():
        setattr(project_settings, key, value)

    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project_settings)

    return ProjectSettingsRead.model_validate(project_settings)
