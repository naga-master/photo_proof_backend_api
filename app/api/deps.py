"""Reusable API dependencies for domain-specific resources."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.orm import Session, selectinload

from app.core.dependencies import get_current_user
from app.db import models
from app.db.session import get_db
from app.schemas import StudioRead, UserRead, UserRole


def get_project(
    project_id: str = Path(..., description="Project identifier"),
    db: Session = Depends(get_db),
) -> models.Project:
    query = (
        db.query(models.Project)
        .options(
            selectinload(models.Project.categories),
            selectinload(models.Project.images).selectinload(models.Image.versions),
            selectinload(models.Project.images).selectinload(models.Image.tags),
            selectinload(models.Project.settings),
            selectinload(models.Project.client),
        )
    )

    project = query.filter(models.Project.id == project_id).first()
    if not project:
        project = query.filter(models.Project.access_url == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def get_project_image(
    image_id: str = Path(..., description="Project image identifier"),
    db: Session = Depends(get_db),
) -> models.Image:
    image = (
        db.query(models.Image)
        .options(selectinload(models.Image.versions), selectinload(models.Image.tags))
        .filter(models.Image.id == image_id)
        .first()
    )
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return image


def get_studio(
    studio_id: str = Path(..., description="Studio identifier"),
    db: Session = Depends(get_db),
) -> models.Studio:
    studio = db.query(models.Studio).filter(models.Studio.id == studio_id).first()
    if not studio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Studio not found")
    return studio


def ensure_studio_access(
    studio: models.Studio = Depends(get_studio),
    current_user: UserRead = Depends(get_current_user),
) -> StudioRead:
    if current_user.role == UserRole.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return StudioRead.model_validate(studio)
