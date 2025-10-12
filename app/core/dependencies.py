"""Common application dependencies."""

from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import models
from app.db.session import get_db
from app.schemas import UserRead, UserRole


logger = logging.getLogger(__name__)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> UserRead:
    """Resolve the authenticated user from the request headers."""

    user_id = request.headers.get("x-user-id")
    if not user_id:
        logger.warning("Missing authentication header for request")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    logger.debug("Resolving current user for request", extra={"user_id": user_id})
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        logger.error("Authenticated user not found", extra={"user_id": user_id})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authenticated user not found")

    logger.debug("Current user resolved", extra={"user_id": user.id})
    return UserRead.model_validate(user)
