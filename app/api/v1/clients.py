"""Client management endpoints."""

from __future__ import annotations

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


router = APIRouter(prefix="/api/clients", tags=["Clients"])


def _client_query(db: Session, studio_id: str):
    return db.query(models.Client).filter(models.Client.studio_id == studio_id)


@router.get("/", response_model=List[ClientRead])
def list_clients(
    search: Optional[str] = Query(None, description="Filter by name, email, or phone"),
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ClientRead]:
    if not current_user.studio_id:
        return []

    query = _client_query(db, current_user.studio_id).order_by(models.Client.created_at.desc())

    if search:
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
    return [ClientRead.model_validate(client) for client in clients]


@router.post("/", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(
    request: CreateClientRequest,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClientRead:
    if current_user.role == UserRole.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create clients")

    if not current_user.studio_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Studio assignment required")

    normalized_email = request.email.lower()

    duplicate_filters = [func.lower(models.Client.email) == normalized_email]
    if request.phone:
        duplicate_filters.append(models.Client.phone == request.phone)

    duplicate = _client_query(db, current_user.studio_id).filter(or_(*duplicate_filters)).first()

    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A client with this email or phone already exists. Choose an existing client or use different details.",
        )

    timestamp = datetime.utcnow()

    client = models.Client(
        id=str(uuid.uuid4()),
        studio_id=current_user.studio_id,
        user_id=None,
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

    return ClientRead.model_validate(client)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: str,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    if current_user.role == UserRole.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete clients")

    if not current_user.studio_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Studio assignment required")

    client = _client_query(db, current_user.studio_id).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    db.delete(client)
    db.commit()
