"""Studio users management router - invite, list, update, delete studio team members."""

import secrets
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, Studio
from app.core.dependencies import get_current_user
from app.services.auth_service import AuthService


router = APIRouter(prefix="/api/studio/users", tags=["Studio Users"])


# Pydantic schemas
class InviteUserRequest(BaseModel):
    email: EmailStr
    name: str
    role: str  # studio_admin, studio_photographer
    

class InviteUserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    invitation_token: str
    invitation_link: str
    message: str


class StudioUserResponse(BaseModel):
    id: str
    email: str
    name: str
    username: str
    role: str
    avatar_url: Optional[str] = None
    is_active: bool
    invitation_accepted: bool
    invitation_sent_at: Optional[str] = None
    last_login_at: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class AcceptInvitationRequest(BaseModel):
    token: str
    password: str


class AcceptInvitationResponse(BaseModel):
    message: str
    user: StudioUserResponse


def generate_invitation_token() -> str:
    """Generate a secure random invitation token."""
    return secrets.token_urlsafe(32)


@router.get("", response_model=List[StudioUserResponse])
def list_studio_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all users belonging to the current user's studio."""
    if not current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must belong to a studio to view users"
        )
    
    # Only studio_owner can list users
    if current_user.role != "studio_owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view studio users"
        )
    
    # Use raw SQL to get invitation fields that may not be in cached model
    from sqlalchemy import text
    
    result = db.execute(text("""
        SELECT id, email, name, username, role, avatar_url, is_active, 
               password_hash, invitation_accepted_at, invitation_sent_at, 
               last_login_at, created_at
        FROM users 
        WHERE studio_id = :studio_id
    """), {"studio_id": current_user.studio_id})
    
    users = result.fetchall()
    
    return [
        StudioUserResponse(
            id=u.id,
            email=u.email,
            name=u.name,
            username=u.username,
            role=u.role,
            avatar_url=u.avatar_url,
            is_active=u.is_active,
            invitation_accepted=u.invitation_accepted_at is not None or u.password_hash is not None,
            invitation_sent_at=u.invitation_sent_at.isoformat() if u.invitation_sent_at else None,
            last_login_at=u.last_login_at.isoformat() if u.last_login_at else None,
            created_at=u.created_at.isoformat() if u.created_at else datetime.utcnow().isoformat()
        )
        for u in users
    ]


@router.post("", response_model=InviteUserResponse)
def invite_user(
    request: InviteUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Invite a new user to the studio."""
    if not current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must belong to a studio to invite users"
        )
    
    # Only studio_owner can invite users
    if current_user.role != "studio_owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to invite users"
        )
    
    # Validate role
    valid_roles = ["studio_admin", "studio_photographer"]
    if request.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )
    
    # Generate invitation token
    invitation_token = generate_invitation_token()
    
    # Create user without password
    new_user = User(
        email=request.email,
        username=request.email,  # Use email as username initially
        name=request.name,
        role=request.role,
        studio_id=current_user.studio_id,
        password_hash=None,  # No password until invitation is accepted
        is_active=True,
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Set invitation fields via raw SQL (to avoid model caching issues)
    from sqlalchemy import text
    db.execute(
        text("UPDATE users SET invitation_token = :token, invitation_sent_at = :sent_at, invited_by_id = :invited_by WHERE id = :user_id"),
        {"token": invitation_token, "sent_at": datetime.utcnow(), "invited_by": current_user.id, "user_id": new_user.id}
    )
    db.commit()
    
    # Get studio for the invitation link
    studio = db.query(Studio).filter(Studio.id == current_user.studio_id).first()
    subdomain = studio.subdomain if studio else "app"
    
    # Generate invitation link (frontend URL)
    # In production, this should come from config
    invitation_link = f"http://{subdomain}.photoapp.local:3001/accept-invitation?token={invitation_token}"
    
    # Send invitation email
    from app.services.email_service import EmailService
    import logging
    logger = logging.getLogger(__name__)
    
    email_sent = EmailService.send_invitation_email(
        to=request.email,
        user_name=request.name,
        role=request.role,
        invitation_url=invitation_link,
        studio_name=studio.name if studio else "Photo Studio",
        invited_by_name=current_user.name,
        studio_logo_url=studio.logo_url if studio else None,
        brand_color=studio.brand_color if studio and studio.brand_color else "#0a58d0",
        reply_to=current_user.email
    )
    
    if email_sent:
        logger.info(f"Invitation email sent to {request.email}")
        message = f"Invitation sent to {request.email}. They will receive an email with instructions to set up their account."
    else:
        logger.warning(f"Failed to send invitation email to {request.email}")
        message = f"Invitation created for {request.email}. Email could not be sent - please share the invitation link manually."
    
    return InviteUserResponse(
        id=new_user.id,
        email=new_user.email,
        name=new_user.name,
        role=new_user.role,
        invitation_token=invitation_token,
        invitation_link=invitation_link,
        message=message
    )


@router.patch("/{user_id}", response_model=StudioUserResponse)
def update_user(
    user_id: str,
    request: UpdateUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a studio user's details."""
    if not current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must belong to a studio"
        )
    
    # Only studio_owner can update users
    if current_user.role != "studio_owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update users"
        )
    
    # Find the user
    user = db.query(User).filter(
        User.id == user_id,
        User.studio_id == current_user.studio_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent demoting the studio owner
    if user.role == "studio_owner" and request.role and request.role != "studio_owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change the role of the studio owner"
        )
    
    # Update fields using raw SQL to avoid model cache issues
    from sqlalchemy import text
    
    update_parts = []
    params = {"user_id": user_id}
    
    if request.name is not None:
        update_parts.append("name = :name")
        params["name"] = request.name
    if request.role is not None:
        update_parts.append("role = :role")
        params["role"] = request.role
    if request.is_active is not None:
        update_parts.append("is_active = :is_active")
        params["is_active"] = request.is_active
    
    if update_parts:
        query = f"UPDATE users SET {', '.join(update_parts)} WHERE id = :user_id"
        db.execute(text(query), params)
        db.commit()
    
    # Fetch updated user data with raw SQL
    result = db.execute(
        text("""
            SELECT id, email, name, username, role, avatar_url, is_active, 
                   password_hash, invitation_accepted_at, invitation_sent_at, 
                   last_login_at, created_at
            FROM users WHERE id = :user_id
        """),
        {"user_id": user_id}
    )
    updated_user = result.fetchone()
    
    return StudioUserResponse(
        id=updated_user.id,
        email=updated_user.email,
        name=updated_user.name,
        username=updated_user.username,
        role=updated_user.role,
        avatar_url=updated_user.avatar_url,
        is_active=updated_user.is_active,
        invitation_accepted=updated_user.invitation_accepted_at is not None or updated_user.password_hash is not None,
        invitation_sent_at=updated_user.invitation_sent_at.isoformat() if updated_user.invitation_sent_at else None,
        last_login_at=updated_user.last_login_at.isoformat() if updated_user.last_login_at else None,
        created_at=updated_user.created_at.isoformat() if updated_user.created_at else datetime.utcnow().isoformat()
    )


@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a studio user."""
    if not current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must belong to a studio"
        )
    
    # Only studio_owner can delete users
    if current_user.role != "studio_owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the studio owner can delete users"
        )
    
    # Find the user
    user = db.query(User).filter(
        User.id == user_id,
        User.studio_id == current_user.studio_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deleting the studio owner
    if user.role == "studio_owner":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the studio owner"
        )
    
    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}


@router.post("/{user_id}/resend-invitation", response_model=InviteUserResponse)
def resend_invitation(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resend invitation to a user who hasn't accepted yet."""
    if not current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must belong to a studio"
        )
    
    # Only studio_owner can resend invitations
    if current_user.role != "studio_owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to resend invitations"
        )
    
    # Find the user using raw SQL to access invitation fields
    from sqlalchemy import text
    
    result = db.execute(
        text("SELECT id, email, name, role, invitation_accepted_at, password_hash FROM users WHERE id = :user_id AND studio_id = :studio_id"),
        {"user_id": user_id, "studio_id": current_user.studio_id}
    )
    user = result.fetchone()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if invitation already accepted
    if user.invitation_accepted_at or user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has already accepted the invitation"
        )
    
    # Generate new invitation token and set via raw SQL
    invitation_token = generate_invitation_token()
    
    db.execute(
        text("UPDATE users SET invitation_token = :token, invitation_sent_at = :sent_at WHERE id = :user_id"),
        {"token": invitation_token, "sent_at": datetime.utcnow(), "user_id": user_id}
    )
    
    db.commit()
    
    # Get studio for the invitation link
    studio = db.query(Studio).filter(Studio.id == current_user.studio_id).first()
    subdomain = studio.subdomain if studio else "app"
    
    invitation_link = f"http://{subdomain}.photoapp.local:3001/accept-invitation?token={invitation_token}"
    
    return InviteUserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        invitation_token=invitation_token,
        invitation_link=invitation_link,
        message=f"New invitation created for {user.email}. Share the invitation link with the user."
    )
