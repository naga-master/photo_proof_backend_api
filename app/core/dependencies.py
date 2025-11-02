"""Common application dependencies."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db import models
from app.db.session import get_db
from app.schemas import UserRead, UserRole
from app.services.auth_service import AuthService


logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)  # Make it optional for cookie support


def get_current_user(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> UserRead:
    """Resolve the authenticated user from JWT token in cookie or Authorization header."""
    
    # Try to get token from Authorization header first, then from cookie
    token = None
    if credentials:
        token = credentials.credentials
    elif access_token:
        token = access_token
    
    if not token:
        logger.warning("No authentication token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Decode JWT token
    payload = AuthService.decode_token(token)
    if not payload:
        logger.warning("Invalid or expired JWT token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token"
        )
    
    # Verify token type
    if payload.get("type") != "access":
        logger.warning("Wrong token type provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
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
    user = db.query(models.User).filter(models.User.id == user_id, models.User.is_active == True).first()
    if not user:
        logger.error("Authenticated user not found or inactive", extra={"user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    logger.debug("Current user resolved", extra={"user_id": user.id, "role": user.role})
    return UserRead.model_validate(user)
