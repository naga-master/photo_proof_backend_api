"""Authentication endpoints."""

from __future__ import annotations

import logging

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db import models
from app.db.session import get_db
from app.schemas import UserRead


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/auth", tags=["Auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/login", response_model=UserRead)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> UserRead:
    logger.debug("Attempting login", extra={"email": request.email})

    user = db.query(models.User).filter(models.User.email == request.email.lower()).first()
    if not user or not user.password_hash:
        logger.warning("Invalid login attempt", extra={"email": request.email})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not bcrypt.checkpw(request.password.encode("utf-8"), user.password_hash.encode("utf-8")):
        logger.warning("Invalid password", extra={"email": request.email})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    logger.info("User authenticated", extra={"user_id": user.id})
    return UserRead.model_validate(user)
