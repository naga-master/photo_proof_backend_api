"""Common application dependencies."""

from __future__ import annotations

import logging
from typing import Optional

# Studio roles (any of these can manage studio resources)
STUDIO_ROLES = {"studio", "studio_owner", "studio_admin", "studio_photographer"}


def is_studio_user(role: str) -> bool:
    """Check if user has any studio role."""
    return role in STUDIO_ROLES

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
    
    # Debug logging
    logger.info(f"Auth check - Cookie: {bool(access_token)}, Header: {bool(credentials)}")
    
    # Try to get token from Authorization header first, then from cookie
    token = None
    if credentials:
        token = credentials.credentials
        logger.info("Using token from Authorization header")
    elif access_token:
        token = access_token
        logger.info("Using token from cookie")
    
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
    role = payload.get("role")
    
    if not user_id:
        logger.warning("Token missing user ID (sub claim)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    logger.debug("Resolving current user for request", extra={"user_id": user_id, "role": role})
    
    # Handle client tokens (sub starts with "client_" or role is "client")
    if role == "client" or (isinstance(user_id, str) and user_id.startswith("client_")):
        client_id = payload.get("client_id")
        if not client_id and isinstance(user_id, str) and user_id.startswith("client_"):
            # Extract client ID from sub claim
            try:
                client_id = int(user_id.replace("client_", ""))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid client token"
                )
        
        if not client_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Client ID not found in token"
            )
        
        # Fetch client from database
        client = db.query(models.Client).filter(models.Client.id == client_id).first()
        if not client:
            logger.error("Client not found", extra={"client_id": client_id})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Client not found"
            )
        
        logger.debug("Client user resolved", extra={"client_id": client.id, "email": client.email})
        
        # Return UserRead-compatible object for client
        return UserRead(
            id=f"client_{client.id}",
            email=client.email,
            username=client.username or client.email,
            name=client.name,
            role=UserRole.CLIENT,
            studio_id=client.studio_id,
            is_active=True,
            email_verified=True,
            phone=client.phone,
            avatar_url=client.avatar_url,
            created_at=client.created_at,
            updated_at=client.updated_at
        )
    
    # Regular user lookup
    user = db.query(models.User).filter(models.User.id == user_id, models.User.is_active == True).first()
    if not user:
        logger.error("Authenticated user not found or inactive", extra={"user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    logger.debug("Current user resolved", extra={"user_id": user.id, "role": user.role})
    return UserRead.model_validate(user)
