"""User related endpoints backed by SQLite."""

import logging
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db import models
from app.db.session import get_db
from app.schemas import UserRead


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/", response_model=List[UserRead])
def list_users(db: Session = Depends(get_db)) -> List[UserRead]:
    logger.debug("Listing users")
    users = db.query(models.User).order_by(models.User.created_at.asc()).all()
    logger.debug("Users fetched", extra={"count": len(users)})
    return [UserRead.model_validate(user) for user in users]


@router.get("/me", response_model=UserRead)
def get_current_user_info(current_user: UserRead = Depends(get_current_user)) -> UserRead:
    logger.debug("Returning current user info", extra={"user_id": current_user.id})
    return current_user
