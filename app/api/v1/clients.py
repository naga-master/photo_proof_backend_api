"""Client management endpoints."""

from __future__ import annotations

import logging
import secrets
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db import models
from app.db.session import get_db
from app.schemas import ClientRead, CreateClientRequest, UserRead, UserRole
from app.services.auth_service import AuthService


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/clients", tags=["Clients"])


def _client_query(db: Session, studio_id: str):
    return db.query(models.Client).filter(models.Client.studio_id == studio_id)


@router.get("/", response_model=List[ClientRead])
def list_clients(
    search: Optional[str] = Query(None, description="Filter by name, email, or phone"),
    studio_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ClientRead]:
    if not studio_user.studio_id:
        logger.debug(
            "List clients skipped due to missing studio",
            extra={"user_id": studio_user.id},
        )
        return []

    query = _client_query(db, studio_user.studio_id).order_by(models.Client.created_at.desc())

    if search:
        logger.debug(
            "Filtering clients",
            extra={"studio_id": studio_user.studio_id, "search": search},
        )
        like_pattern = f"%{search.lower()}%"
        phone_filter = models.Client.phone.ilike(like_pattern) if like_pattern else None
        filters = [
            func.lower(models.Client.name).like(like_pattern),
            func.lower(models.Client.email).like(like_pattern),
        ]
        if phone_filter is not None:
            filters.append(phone_filter)
        query = query.filter(or_(*filters))

    clients = query.all()
    logger.debug(
        "Clients retrieved",
        extra={"count": len(clients), "studio_id": studio_user.studio_id},
    )
    return [ClientRead.model_validate(client) for client in clients]


@router.post("/", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(
    request: CreateClientRequest,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClientRead:
    logger.debug(
        "Creating client",
        extra={"user_id": current_user.id, "studio_id": current_user.studio_id},
    )
    if current_user.role == UserRole.CLIENT:
        logger.warning("Client user attempted to create client", extra={"user_id": current_user.id})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create clients")

    if not current_user.studio_id:
        logger.warning("User missing studio assignment during client creation", extra={"user_id": current_user.id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Studio assignment required")

    normalized_email = request.email.lower()

    # Check for duplicate client
    duplicate_filters = [func.lower(models.Client.email) == normalized_email]
    if request.phone:
        duplicate_filters.append(models.Client.phone == request.phone)

    duplicate = _client_query(db, current_user.studio_id).filter(or_(*duplicate_filters)).first()

    if duplicate:
        logger.warning(
            "Duplicate client encountered",
            extra={"studio_id": current_user.studio_id, "email": normalized_email},
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A client with this email or phone already exists. Choose an existing client or use different details.",
        )
    
    # Check for duplicate user email
    existing_user = db.query(models.User).filter(func.lower(models.User.email) == normalized_email).first()
    if existing_user:
        logger.warning(
            "User account with email already exists",
            extra={"email": normalized_email, "existing_user_id": existing_user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user account with this email already exists.",
        )

    timestamp = datetime.utcnow()

    # Generate random password for new client user account
    random_password = secrets.token_urlsafe(12)  # Generates a secure random password
    
    # Create user account first
    user_id = str(uuid.uuid4())
    user = models.User(
        id=user_id,
        studio_id=current_user.studio_id,
        name=request.name,
        email=normalized_email,
        username=normalized_email,  # Use email as username
        password_hash=AuthService.hash_password(random_password),
        role="client",
        is_active=True,
        email_verified=False,
        created_at=timestamp,
        updated_at=timestamp,
    )
    db.add(user)
    
    # Create client record linked to user
    client = models.Client(
        id=str(uuid.uuid4()),
        studio_id=current_user.studio_id,
        user_id=user_id,  # Link to user account
        name=request.name,
        email=normalized_email,
        phone=request.phone,
        status="active",
        total_projects=0,
        created_at=timestamp,
        updated_at=timestamp,
    )

    db.add(client)
    db.commit()
    db.refresh(client)

    logger.info(
        "Client created with user account", 
        extra={
            "client_id": client.id, 
            "user_id": user_id,
            "studio_id": current_user.studio_id,
            "email": normalized_email,
            "password": random_password  # Log password for studio to share with client
        }
    )
    
    # TODO: Send email to client with their credentials
    # TODO: Or display password in response for studio to share
    
    return ClientRead.model_validate(client)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: str,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    logger.debug(
        "Deleting client",
        extra={"client_id": client_id, "user_id": current_user.id},
    )
    if current_user.role == UserRole.CLIENT:
        logger.warning("Client user attempted to delete client", extra={"user_id": current_user.id})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete clients")

    if not current_user.studio_id:
        logger.warning("User missing studio assignment during client deletion", extra={"user_id": current_user.id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Studio assignment required")

    client = _client_query(db, current_user.studio_id).filter(models.Client.id == client_id).first()
    if not client:
        logger.warning(
            "Client not found for deletion",
            extra={"client_id": client_id, "studio_id": current_user.studio_id},
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    db.delete(client)
    db.commit()
    logger.info("Client deleted", extra={"client_id": client_id, "studio_id": current_user.studio_id})
