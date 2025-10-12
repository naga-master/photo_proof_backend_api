"""Studio related endpoints backed by SQLite."""

import logging
from datetime import datetime
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api import deps
from app.core.dependencies import get_current_user
from app.db import models
from app.db.session import get_db
from app.schemas import CreateStudioRequest, StudioRead, UserRead, UserRole


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/studios", tags=["Studios"])


@router.get("/", response_model=List[StudioRead])
def list_studios(db: Session = Depends(get_db)) -> List[StudioRead]:
    logger.debug("Listing studios")
    studios = db.query(models.Studio).order_by(models.Studio.created_at.asc()).all()
    logger.debug("Studios fetched", extra={"count": len(studios)})
    return [StudioRead.model_validate(studio) for studio in studios]


@router.post("/", response_model=StudioRead, status_code=status.HTTP_201_CREATED)
def create_studio(request: CreateStudioRequest, db: Session = Depends(get_db)) -> StudioRead:
    logger.debug("Creating studio", extra={"email": request.email})
    studio = models.Studio(
        id=str(uuid4()),
        name=request.name,
        business_name=request.business_name,
        email=request.email.lower(),
        phone=request.phone,
        website=request.website,
        address_line1=request.address_line1,
        address_line2=request.address_line2,
        city=request.city,
        state=request.state,
        postal_code=request.postal_code,
        country=request.country,
        logo_url=request.logo_url,
        brand_color=request.brand_color,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(studio)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.warning("Studio creation conflict", extra={"email": request.email.lower()})
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Studio with this email already exists")

    db.refresh(studio)
    logger.info("Studio created", extra={"studio_id": studio.id})
    return StudioRead.model_validate(studio)


@router.get("/current", response_model=StudioRead)
def get_current_user_studio(
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudioRead:
    logger.debug("Fetching current user studio", extra={"user_id": current_user.id})
    if not current_user.studio_id:
        logger.info("Current user has no studio", extra={"user_id": current_user.id})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Studio not found")

    studio = db.query(models.Studio).filter(models.Studio.id == current_user.studio_id).first()
    if not studio:
        logger.warning(
            "Studio referenced by user missing",
            extra={"user_id": current_user.id, "studio_id": current_user.studio_id},
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Studio not found")

    return StudioRead.model_validate(studio)


@router.post("/current", response_model=StudioRead, status_code=status.HTTP_201_CREATED)
def create_studio_for_current_user(
    request: CreateStudioRequest,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudioRead:
    if current_user.role == UserRole.CLIENT.value:
        logger.warning("Client attempted to create studio", extra={"user_id": current_user.id})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only studio users can create studios")

    logger.debug("Creating studio for current user", extra={"user_id": current_user.id})

    existing_studio = None
    if current_user.studio_id:
        existing_studio = db.query(models.Studio).filter(models.Studio.id == current_user.studio_id).first()
    if existing_studio:
        logger.info(
            "Studio already exists for user",
            extra={"user_id": current_user.id, "studio_id": existing_studio.id},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Studio already exists")

    studio = models.Studio(
        id=str(uuid4()),
        name=request.name,
        business_name=request.business_name,
        email=request.email.lower(),
        phone=request.phone,
        website=request.website,
        address_line1=request.address_line1,
        address_line2=request.address_line2,
        city=request.city,
        state=request.state,
        postal_code=request.postal_code,
        country=request.country,
        logo_url=request.logo_url,
        brand_color=request.brand_color,
        subscription_tier="free",
        subscription_status="trial",
        max_projects=5,
        max_storage_gb=10,
        storage_used_bytes=0,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(studio)

    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if user:
        user.studio_id = studio.id
        user.updated_at = datetime.utcnow()

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.warning(
            "Studio creation conflict for current user",
            extra={"user_id": current_user.id, "email": request.email.lower()},
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Studio with this email already exists")

    db.refresh(studio)
    logger.info(
        "Studio created for current user",
        extra={"user_id": current_user.id, "studio_id": studio.id},
    )
    return StudioRead.model_validate(studio)


@router.get("/{studio_id}", response_model=StudioRead)
def get_studio(studio: models.Studio = Depends(deps.get_studio)) -> StudioRead:
    logger.debug("Returning studio", extra={"studio_id": studio.id})
    return StudioRead.model_validate(studio)
