"""Common application dependencies."""

from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db import models
from app.db.session import get_db
from app.schemas import UserRead, UserRole
from app.services.auth_service import AuthService


logger = logging.getLogger(__name__)
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> UserRead:
    """Resolve the authenticated user from JWT token in Authorization header."""
    
    # Extract token from credentials
    token = credentials.credentials
    
    # Decode JWT token
    payload = AuthService.decode_token(token)
    if not payload:
        logger.warning("Invalid or expired JWT token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token"
        )
    
    # Extract user ID from token payload
    user_id = payload.get("sub")
    if not user_id:
        logger.warning("Token missing user ID (sub claim)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    logger.debug("Resolving current user for request", extra={"user_id": user_id})
    
    # Fetch user from database
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        logger.error("Authenticated user not found", extra={"user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    logger.debug("Current user resolved", extra={"user_id": user.id, "role": user.role})
    return UserRead.model_validate(user)
