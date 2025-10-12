"""Common application dependencies."""

from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import models
from app.db.session import get_db
from app.schemas import UserRead, UserRole


logger = logging.getLogger(__name__)


def get_current_user(db: Session = Depends(get_db)) -> UserRead:
    """Return a representative authenticated user for demo purposes."""

    logger.debug("Resolving current user for request")
    user = (
        db.query(models.User)
        .filter(models.User.role.in_([UserRole.STUDIO_OWNER.value, UserRole.STUDIO_ADMIN.value]))
        .order_by(models.User.created_at.asc())
        .first()
    )
    if not user:
        logger.error("No eligible user found for request context")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authenticated user not found")

    logger.debug("Current user resolved", extra={"user_id": user.id})
    return UserRead.model_validate(user)
