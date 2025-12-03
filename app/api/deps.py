"""Reusable API dependencies for domain-specific resources."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Path, Request, status
from sqlalchemy.orm import Session, selectinload

from app.core.dependencies import get_current_user
from app.db import models
from app.db.session import get_db
from app.schemas import StudioRead, UserRead, UserRole
from app.middleware.tenant import TenantContext


logger = logging.getLogger(__name__)


def get_project(
    project_id: str = Path(..., description="Project identifier"),
    db: Session = Depends(get_db),
) -> models.Project:
    logger.debug("Resolving project dependency", extra={"project_id": project_id})
    
    # Convert project_id to integer (Project model uses Integer ID)
    try:
        project_id_int = int(project_id)
    except ValueError:
        # Check if it's a UUID format (from old frontend mock data)
        if len(project_id) == 36 and project_id.count('-') == 4:
            logger.warning("UUID project ID received (old mock data)", extra={"project_id": project_id})
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found. This appears to be mock data. Please refresh the project list."
            )
        logger.warning("Invalid project ID format", extra={"project_id": project_id})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID format. Expected numeric ID."
        )
    
    # Query with actual relationships that exist in Project model
    query = (
        db.query(models.Project)
        .options(
            selectinload(models.Project.client),
            selectinload(models.Project.photos),
            selectinload(models.Project.folders),
        )
    )

    project = query.filter(models.Project.id == project_id_int).first()
    if not project:
        logger.warning("Project not found", extra={"project_id": project_id})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    logger.debug("Project dependency resolved", extra={"project_id": project.id})
    return project


def get_project_image(
    image_id: str = Path(..., description="Project image/photo identifier"),
    db: Session = Depends(get_db),
) -> models.Photo:
    """
    Get a photo by ID. Note: Changed from Image to Photo model.
    """
    logger.debug("Resolving project photo", extra={"photo_id": image_id})
    
    # Convert image_id to integer (Photo model uses Integer ID)
    try:
        photo_id_int = int(image_id)
    except ValueError:
        logger.warning("Invalid photo ID format", extra={"photo_id": image_id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid photo ID format")
    
    photo = (
        db.query(models.Photo)
        .filter(models.Photo.id == photo_id_int)
        .first()
    )
    if not photo:
        logger.warning("Photo not found", extra={"photo_id": image_id})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    logger.debug("Project photo resolved", extra={"photo_id": photo.id})
    return photo


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


def get_current_studio_user(
    current_user: UserRead = Depends(get_current_user),
) -> UserRead:
    """Ensure the current user is a studio user (not a client)."""
    if current_user.role == UserRole.CLIENT:
        logger.warning("Client attempted to access studio-only resource", extra={"user_id": current_user.id})
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Studio access required"
        )
    logger.debug("Studio user access validated", extra={"user_id": current_user.id})
    return current_user


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


# ========== Multi-Tenant Dependencies ==========

def get_current_studio(request: Request) -> models.Studio:
    """Get current studio from request state (set by tenant middleware).
    
    Raises HTTPException if no studio is found for the current domain.
    Use this for endpoints that REQUIRE a studio context.
    """
    studio = TenantContext.get_studio_from_request(request)
    
    if not studio:
        logger.error("No studio found in request context")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Studio not found for this domain. Please ensure you're accessing via a valid studio domain."
        )
    
    logger.debug(f"Studio resolved from request: {studio.name} ({studio.id})")
    return studio


def get_optional_studio(request: Request) -> Optional[models.Studio]:
    """Get current studio if available (doesn't raise exception).
    
    Use this for endpoints that can work with or without a studio context.
    """
    studio = TenantContext.get_studio_from_request(request)
    if studio:
        logger.debug(f"Optional studio resolved: {studio.name} ({studio.id})")
    else:
        logger.debug("No studio in request context (optional)")
    return studio


def require_studio_user(
    user: UserRead = Depends(get_current_user),
    studio: models.Studio = Depends(get_current_studio)
) -> UserRead:
    """Ensure user belongs to current studio (from domain).
    
    This enforces both:
    1. User is authenticated
    2. User belongs to the studio determined by the domain
    
    Use this for studio-specific operations to prevent cross-tenant access.
    """
    # Check if user belongs to this studio
    if user.studio_id != studio.id:
        logger.warning(
            f"User {user.id} attempted to access studio {studio.id} but belongs to {user.studio_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this studio's resources"
        )
    
    logger.debug(f"Studio user access validated: {user.email} for studio {studio.name}")
    return user


def get_tenant_db(
    db: Session = Depends(get_db),
    studio: models.Studio = Depends(get_current_studio)
) -> tuple[Session, models.Studio]:
    """Get database session with studio context.
    
    Returns tuple of (db, studio) for convenience in endpoints.
    Use this when you need both the database session and studio context.
    """
    return db, studio
