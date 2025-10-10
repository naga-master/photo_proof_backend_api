"""Studio related endpoints backed by SQLite."""

from datetime import datetime
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api import deps
from app.db import models
from app.db.session import get_db
from app.schemas import StudioRead


router = APIRouter(prefix="/api/studios", tags=["Studios"])


@router.get("/", response_model=List[StudioRead])
def list_studios(db: Session = Depends(get_db)) -> List[StudioRead]:
    studios = db.query(models.Studio).order_by(models.Studio.created_at.asc()).all()
    return [StudioRead.model_validate(studio) for studio in studios]


@router.post("/", response_model=StudioRead)
def create_studio(studio_data: dict, db: Session = Depends(get_db)) -> StudioRead:
    name = studio_data.get("name")
    email = studio_data.get("email")
    if not name or not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name and email are required")

    studio = models.Studio(
        id=str(uuid4()),
        name=name,
        business_name=studio_data.get("business_name"),
        email=email.lower(),
        phone=studio_data.get("phone"),
        website=studio_data.get("website"),
        address_line1=studio_data.get("address_line1"),
        address_line2=studio_data.get("address_line2"),
        city=studio_data.get("city"),
        state=studio_data.get("state"),
        postal_code=studio_data.get("postal_code"),
        country=studio_data.get("country"),
        logo_url=studio_data.get("logo_url"),
        brand_color=studio_data.get("brand_color"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(studio)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Studio with this email already exists")

    db.refresh(studio)
    return StudioRead.model_validate(studio)


@router.get("/{studio_id}", response_model=StudioRead)
def get_studio(studio: models.Studio = Depends(deps.get_studio)) -> StudioRead:
    return StudioRead.model_validate(studio)
