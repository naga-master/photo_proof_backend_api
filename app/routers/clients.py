"""Clients router with CRUD operations."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.db.session import get_db
from app.db.models import Client, User
from app.schemas.auth import ClientCreate, ClientUpdate, ClientResponse
from app.api.deps import get_current_user
from app.services.auth_service import AuthService


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[ClientResponse])
def list_clients(
    search: Optional[str] = Query(None, description="Search by name or email"),
    status_filter: Optional[str] = Query(None, description="Filter by status: active, inactive, archived"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Client]:
    """
    List all clients for the current studio.
    
    Only studio users can access this endpoint.
    Supports search by name/email and filtering by status.
    """
    print("\n" + "="*80)
    logger.debug("[CLIENTS DEBUG] list_clients endpoint called")
    print("="*80 + "\n")
    # Only studio users can list clients
    if not current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can list clients"
        )
    
    # Base query filtered by studio with eager loading of projects for counting
    query = db.query(Client).filter(Client.studio_id == current_user.studio_id).options(
        joinedload(Client.projects)
    )
    
    # Filter out clients with invalid data (empty name or email)
    # This prevents validation errors when returning data
    query = query.filter(
        Client.name != "",
        Client.name.isnot(None),
        Client.email != "",
        Client.email.isnot(None),
        Client.email.contains("@")  # Basic email validation
    )
    
    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Client.name.ilike(search_pattern),
                Client.email.ilike(search_pattern)
            )
        )
    
    # Apply status filter
    if status_filter:
        query = query.filter(Client.status == status_filter)
    
    # Order by most recent first
    query = query.order_by(Client.created_at.desc())
    
    # Apply pagination
    clients = query.offset(skip).limit(limit).all()
    
    # Add project counts to responses
    result = []
    for client in clients:
        # Create response with computed project count
        client_dict = ClientResponse.model_validate(client).model_dump()
        client_dict['total_projects'] = len(client.projects) if client.projects else 0
        result.append(ClientResponse(**client_dict))
        logger.debug(f"[CLIENTS DEBUG] Client {client.id} ({client.name}): {client_dict['total_projects']} projects")
    
    logger.debug(f"[CLIENTS DEBUG] Returning {len(result)} clients with project counts\n")
    return result


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Client:
    """
    Get a specific client by ID.
    
    Studio users can access any client in their studio.
    Clients can only access their own profile.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Check access permissions
    # Studio users can access all their clients
    if current_user.studio_id == client.studio_id:
        return client
    
    # Clients can access their own profile
    if current_user.client_profile and current_user.client_profile.id == client_id:
        return client
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to access this client"
    )


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    client_data: ClientCreate,
    force: bool = Query(False, description="Force creation even if phone exists"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Client:
    """
    Create a new client for the current studio.
    
    Only studio users can create clients.
    If username/password provided, also creates a User account.
    """
    # Only studio users can create clients
    if not current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can create clients"
        )
    
    # Validate required fields
    if not client_data.name or len(client_data.name.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client name must be at least 2 characters"
        )
    
    if not client_data.email or '@' not in client_data.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid email address is required"
        )
    
    # Check if email already exists for this studio
    existing_client = (
        db.query(Client)
        .filter(
            Client.studio_id == current_user.studio_id,
            Client.email == client_data.email
        )
        .first()
    )
    
    if existing_client:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client with this email already exists"
        )
    
    # Check for duplicate phone number (warning only, unless force=True)
    if client_data.phone and not force:
        existing_phone = (
            db.query(Client)
            .filter(
                Client.studio_id == current_user.studio_id,
                Client.phone == client_data.phone
            )
            .first()
        )
        
        if existing_phone:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "duplicate_detected",
                    "type": "client_phone",
                    "message": "A client with this phone number already exists",
                    "existing_client": {
                        "id": existing_phone.id,
                        "name": existing_phone.name,
                        "email": existing_phone.email
                    },
                    "actions": ["use_existing", "create_anyway"]
                }
            )
    
    # Check if username is unique (if provided)
    if client_data.username:
        existing_username = (
            db.query(Client)
            .filter(Client.username == client_data.username)
            .first()
        )
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Create client
    client = Client(
        studio_id=current_user.studio_id,
        name=client_data.name,
        email=client_data.email,
        phone=client_data.phone,
        address=client_data.address,
        username=client_data.username,
        password=AuthService.hash_password(client_data.password) if client_data.password else None,
        whatsapp_opt_in=client_data.whatsapp_opt_in,
        email_opt_in=client_data.email_opt_in,
        status="active"
    )
    
    db.add(client)
    db.commit()
    db.refresh(client)
    
    # TODO: Optionally create User account if username/password provided
    # This would allow client to log in to the system
    
    return client


@router.patch("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    client_update: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Client:
    """
    Update a client's information.
    
    Studio users can update any client in their studio.
    Clients can update their own profile.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Check update permissions
    can_update = False
    
    # Studio users can update their clients
    if current_user.studio_id == client.studio_id:
        can_update = True
    
    # TODO: Allow clients to update their own profile when client login is implemented
    # if hasattr(current_user, 'client_profile') and current_user.client_profile and current_user.client_profile.id == client_id:
    #     can_update = True
    
    if not can_update:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this client"
        )
    
    # Update fields
    update_data = client_update.model_dump(exclude_unset=True)
    
    # Check email uniqueness if being updated
    if "email" in update_data and update_data["email"] != client.email:
        existing_email = (
            db.query(Client)
            .filter(
                Client.studio_id == client.studio_id,
                Client.email == update_data["email"],
                Client.id != client_id
            )
            .first()
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
    
    # Apply updates
    for field, value in update_data.items():
        setattr(client, field, value)
    
    db.commit()
    db.refresh(client)
    
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a client.
    
    Only studio users can delete clients.
    This will cascade delete all related projects and data.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Only studio users can delete
    if current_user.studio_id != client.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can delete clients"
        )
    
    db.delete(client)
    db.commit()


@router.patch("/{client_id}/archive", response_model=ClientResponse)
def archive_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Client:
    """
    Archive a client (soft delete).
    
    Sets status to 'archived' instead of deleting.
    Only studio users can archive clients.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Only studio users can archive
    if current_user.studio_id != client.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can archive clients"
        )
    
    client.status = "archived"
    db.commit()
    db.refresh(client)
    
    return client


@router.patch("/{client_id}/activate", response_model=ClientResponse)
def activate_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Client:
    """
    Activate an archived or inactive client.
    
    Sets status to 'active'.
    Only studio users can activate clients.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Only studio users can activate
    if current_user.studio_id != client.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can activate clients"
        )
    
    client.status = "active"
    db.commit()
    db.refresh(client)
    
    return client
