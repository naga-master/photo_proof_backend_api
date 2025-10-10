"""Reusable API dependencies for domain-specific resources."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Path, status

from app.core.dependencies import get_current_user, get_data_manager
from app.schemas import Project, ProjectImage, Studio, User, UserRole
from app.services.data_manager import DataManager


async def get_project(
    project_id: str = Path(..., description="Project identifier"),
    data_manager: DataManager = Depends(get_data_manager),
) -> Project:
    project = data_manager.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


async def get_project_image(
    image_id: str = Path(..., description="Project image identifier"),
    project: Project = Depends(get_project),
) -> ProjectImage:
    image = next((img for img in project.images if img.id == image_id), None)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return image


async def get_studio(
    studio_id: str = Path(..., description="Studio identifier"),
    data_manager: DataManager = Depends(get_data_manager),
) -> Studio:
    studio = data_manager.get_studio_by_id(studio_id)
    if not studio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Studio not found")
    return studio


async def ensure_studio_access(
    studio: Studio = Depends(get_studio),
    current_user: User = Depends(get_current_user),
) -> Studio:
    if current_user.role != UserRole.STUDIO or current_user.studio_id != studio.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return studio
