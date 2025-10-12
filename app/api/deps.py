"""Reusable API dependencies for domain-specific resources."""

from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.orm import Session, selectinload

from app.core.dependencies import get_current_user
from app.db import models
from app.db.session import get_db
from app.schemas import StudioRead, UserRead, UserRole


logger = logging.getLogger(__name__)


def get_project(
    project_id: str = Path(..., description="Project identifier"),
    db: Session = Depends(get_db),
) -> models.Project:
    logger.debug("Resolving project dependency", extra={"project_id": project_id})
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
        logger.warning("Project not found", extra={"project_id": project_id})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    logger.debug("Project dependency resolved", extra={"project_id": project.id})
    return project


def get_project_image(
    image_id: str = Path(..., description="Project image identifier"),
    db: Session = Depends(get_db),
) -> models.Image:
    logger.debug("Resolving project image", extra={"image_id": image_id})
    image = (
        db.query(models.Image)
        .options(selectinload(models.Image.versions), selectinload(models.Image.tags))
        .filter(models.Image.id == image_id)
        .first()
    )
    if not image:
        logger.warning("Image not found", extra={"image_id": image_id})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    logger.debug("Project image resolved", extra={"image_id": image.id})
    return image


def get_studio(
    studio_id: str = Path(..., description="Studio identifier"),
    db: Session = Depends(get_db),
) -> models.Studio:
    logger.debug("Resolving studio dependency", extra={"studio_id": studio_id})
    studio = db.query(models.Studio).filter(models.Studio.id == studio_id).first()
    if not studio:
        logger.warning("Studio not found", extra={"studio_id": studio_id})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Studio not found")
    logger.debug("Studio dependency resolved", extra={"studio_id": studio.id})
    return studio


def ensure_studio_access(
    studio: models.Studio = Depends(get_studio),
    current_user: UserRead = Depends(get_current_user),
) -> StudioRead:
    if current_user.role == UserRole.CLIENT:
        logger.warning("Client attempted to access studio resource", extra={"user_id": current_user.id})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    logger.debug(
        "Studio access granted",
        extra={"studio_id": studio.id, "user_id": current_user.id},
    )
    return StudioRead.model_validate(studio)
