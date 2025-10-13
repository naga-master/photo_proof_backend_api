"""Authentication endpoints."""

from __future__ import annotations

import base64
import logging
from datetime import datetime
from uuid import uuid4

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import models
from app.db.session import get_db
from app.schemas import (
    StudioOnboardingRequest,
    StudioOnboardingResponse,
    StudioRead,
    UserRead,
    UserRole,
)


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    encoding: str | None = "plain"


def _decode_password(value: str, encoding: str | None) -> str:
    password_encoding = (encoding or "plain").lower()

    if password_encoding == "plain":
        return value

    if password_encoding == "base64":
        try:
            return base64.b64decode(value.encode("utf-8")).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as decode_error:
            logger.warning("Invalid base64 password encoding", exc_info=decode_error)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password encoding",
            ) from decode_error

    logger.warning("Unsupported password encoding provided", extra={"encoding": encoding})
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported password encoding")


@router.post("/login", response_model=UserRead)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> UserRead:
    logger.debug("Attempting login", extra={"email": request.email})

    password = _decode_password(request.password, request.encoding)

    user = db.query(models.User).filter(models.User.email == request.email.lower()).first()
    if not user or not user.password_hash:
        logger.warning("Invalid login attempt", extra={"email": request.email})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
        logger.warning("Invalid password", extra={"email": request.email})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    logger.info("User authenticated", extra={"user_id": user.id})
    return UserRead.model_validate(user)


@router.post("/onboard", response_model=StudioOnboardingResponse, status_code=status.HTTP_201_CREATED)
def onboard_studio(request: StudioOnboardingRequest, db: Session = Depends(get_db)) -> StudioOnboardingResponse:
    email = request.email.lower().strip()
    password = _decode_password(request.password, getattr(request, "password_encoding", None))
    password_confirm = _decode_password(request.password_confirm, getattr(request, "password_encoding", None))

    if password != password_confirm:
        logger.warning("Password mismatch during onboarding", extra={"email": email})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

    existing_user = db.query(models.User).filter(models.User.email == email).first()
    if existing_user:
        logger.info("Onboarding attempted for existing user", extra={"email": email})
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")

    existing_studio = db.query(models.Studio).filter(models.Studio.email == email).first()
    if existing_studio:
        logger.info("Onboarding attempted for existing studio", extra={"email": email})
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Studio with this email already exists")

    studio = models.Studio(
        id=str(uuid4()),
        name=request.name,
        business_name=request.business_name,
        email=email,
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

    user = models.User(
        id=str(uuid4()),
        studio_id=studio.id,
        name=request.owner_name or request.name,
        email=email,
        password_hash=bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
        role=UserRole.STUDIO_OWNER.value,
        avatar_url=None,
        phone=request.phone,
        last_login_at=None,
        email_verified=True,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(studio)
    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.exception("Failed to onboard studio due to integrity error", extra={"email": email})
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Unable to onboard studio with provided details")

    db.refresh(studio)
    db.refresh(user)

    logger.info("Studio onboarded successfully", extra={"studio_id": studio.id, "user_id": user.id})
    return StudioOnboardingResponse(
        studio=StudioRead.model_validate(studio),
        user=UserRead.model_validate(user),
    )
