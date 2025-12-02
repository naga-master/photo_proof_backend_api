"""Authentication router."""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.db.session import get_db
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user
from app.core.config import get_settings
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    StudioResponse,
    ClientResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from app.schemas import UserRead
from app.services.email_service import EmailService


router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()


@router.options("/studio/login")
async def studio_login_options():
    """Handle CORS preflight for studio login."""
    return {"ok": True}


@router.options("/client/login")
async def client_login_options():
    """Handle CORS preflight for client login."""
    return {"ok": True}


@router.post("/studio/login", response_model=LoginResponse)
def studio_login(login_data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Studio user login with httpOnly cookie support."""
    import logging
    logger = logging.getLogger(__name__)
    
    result = AuthService.studio_login(db, login_data)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    user, access_token = result
    
    # Debug: Log user permissions from DB
    logger.info(f"[AUTH DEBUG] User {user.email} logging in")
    logger.info(f"[AUTH DEBUG] User role: {user.role}")
    db_permissions = getattr(user, 'permissions', None)
    logger.info(f"[AUTH DEBUG] User permissions from DB: {db_permissions}")
    logger.info(f"[AUTH DEBUG] User permissions type: {type(db_permissions)}")
    
    # Get user's permissions for the refresh token
    from app.services.permission_service import PermissionService
    permissions = PermissionService.get_user_permissions(user)
    
    logger.info(f"[AUTH DEBUG] Effective permissions: {permissions}")
    logger.info(f"[AUTH DEBUG] canViewClients: {permissions.get('canViewClients', 'NOT SET')}")
    
    # Create refresh token with permissions
    token_data = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "studio_id": user.studio_id,
        "permissions": permissions,
    }
    refresh_token = AuthService.create_refresh_token(token_data)
    
    # Set httpOnly cookies for better security
    settings = get_settings()
    
    # Access token - short lived
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path="/",
        max_age=30 * 60  # 30 minutes
    )
    
    # Refresh token - longer lived
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path="/",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    # Build user response with effective permissions (not raw DB permissions)
    user_response = UserResponse.model_validate(user)
    user_response.permissions = permissions  # Override with effective permissions
    
    logger.info(f"[AUTH DEBUG] Response permissions: {user_response.permissions}")
    
    return LoginResponse(
        token=access_token,
        refresh_token=refresh_token,
        user=user_response
    )


@router.post("/client/login", response_model=LoginResponse)
def client_login(login_data: LoginRequest, response: Response, request: Request, db: Session = Depends(get_db)):
    """Client user login with httpOnly cookie support.
    
    Supports both:
    - Direct Client authentication (Client.password) - new simple method
    - Legacy User table authentication (User.password_hash)
    
    Uses studio context from domain for multi-tenant isolation.
    """
    from app.middleware.tenant import TenantContext
    
    # Get studio_id from tenant middleware (domain-based)
    studio_id = TenantContext.get_studio_id_from_request(request)
    
    result = AuthService.client_login(db, login_data, studio_id=studio_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    entity, access_token = result
    
    # Determine if this is a Client or User entity
    from app.db.models import Client, User
    
    if isinstance(entity, Client):
        # Direct Client authentication (new method)
        client = entity
        token_data = {
            "sub": f"client_{client.id}",
            "email": client.email,
            "role": "client",
            "studio_id": client.studio_id,
            "client_id": client.id
        }
        user_response = UserResponse(
            id=str(client.id),
            email=client.email,
            username=client.email,
            name=client.name,
            role="client",
            studio_id=client.studio_id,
            is_active=True,
            email_verified=False,
            phone=client.phone,
            avatar_url=client.avatar_url or client.profile_picture,
            created_at=client.created_at.isoformat() if client.created_at else None,
            updated_at=client.updated_at.isoformat() if client.updated_at else None
        )
        client_id = client.id
    else:
        # Legacy User table authentication
        user = entity
        client = db.query(Client).filter(Client.user_id == user.id).first()
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role,
            "studio_id": user.studio_id,
            "client_id": client.id if client else None
        }
        user_response = UserResponse.model_validate(user)
        client_id = client.id if client else None
    
    refresh_token = AuthService.create_refresh_token(token_data)
    
    # Set httpOnly cookies for better security
    settings = get_settings()
    
    # Access token - short lived
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path="/",
        max_age=30 * 60  # 30 minutes
    )
    
    # Refresh token - longer lived
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path="/",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    return LoginResponse(
        token=access_token,
        refresh_token=refresh_token,
        user=user_response,
        client_id=client_id
    )


@router.post("/studio/register", response_model=LoginResponse)
def register_studio(register_data: RegisterRequest, db: Session = Depends(get_db)):
    """Register new studio account."""
    try:
        studio, access_token = AuthService.register_studio(db, register_data)
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            role="studio",
            user=StudioResponse(
                id=studio.id,
                studio_name=studio.studio_name,
                email=studio.email,
                logo=studio.logo,
                created_at=studio.created_at,
                updated_at=studio.updated_at,
            )
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user.
    Supports both httpOnly cookies and Authorization header.
    """
    from app.services.permission_service import PermissionService
    from app.db.models import User
    
    # Get full user from DB to access permissions
    user = db.query(User).filter(User.id == current_user.id).first()
    permissions = PermissionService.get_user_permissions(user) if user else None
    
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        name=current_user.name,
        role=current_user.role,
        studio_id=str(current_user.studio_id) if current_user.studio_id else None,
        is_active=current_user.is_active,
        email_verified=current_user.email_verified,
        phone=current_user.phone,
        avatar_url=current_user.avatar_url,
        permissions=permissions,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None,
        updated_at=current_user.updated_at.isoformat() if current_user.updated_at else None
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token from httpOnly cookie.
    The refresh_token is automatically sent by the browser in the cookie.
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided"
        )
    
    # Verify refresh token
    payload = AuthService.verify_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_id = payload.get("sub")
    role = payload.get("role")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Handle client tokens (sub starts with "client_" or role is "client")
    if role == "client" or (isinstance(user_id, str) and user_id.startswith("client_")):
        client_id = payload.get("client_id")
        if not client_id and isinstance(user_id, str) and user_id.startswith("client_"):
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
        
        from app.db.models import Client
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Client not found"
            )
        
        # Generate new access token for client
        token_data = {
            "sub": f"client_{client.id}",
            "email": client.email,
            "role": "client",
            "studio_id": client.studio_id,
            "client_id": client.id,
        }
        new_access_token = AuthService.create_access_token(token_data)
    else:
        # Regular user lookup
        from app.db.models import User
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Generate new access token
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role,
            "studio_id": user.studio_id,
        }
        
        if user.role == "client":
            from app.db.models import Client
            client = db.query(Client).filter(Client.user_id == user.id).first()
            if client:
                token_data["client_id"] = client.id
        
        new_access_token = AuthService.create_access_token(token_data)
    
    # Set new access token in cookie
    settings = get_settings()
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path="/",
        max_age=30 * 60  # 30 minutes
    )
    
    return TokenResponse(
        access_token=new_access_token,
        token=new_access_token,  # Backwards compatibility
        token_type="bearer"
    )


@router.post("/logout")
def logout(response: Response):
    """Logout user by clearing authentication cookies."""
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return {"message": "Successfully logged out"}


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Request a password reset email.
    
    Always returns success to prevent email enumeration attacks.
    If the email exists, sends a password reset link.
    """
    import logging
    logger = logging.getLogger(__name__)
    settings = get_settings()
    
    result = AuthService.find_user_by_email(db, request.email)
    
    if result:
        user_type, entity, studio = result
        
        # Get user ID based on type
        if user_type == "user":
            user_id = entity.id
            user_name = entity.name or entity.username
        else:
            user_id = f"client_{entity.id}"
            user_name = entity.name
        
        # Get studio info for branding
        studio_name = studio.name if studio else settings.smtp_from_name
        studio_logo = studio.logo_url if studio else None
        brand_color = studio.brand_color if studio and studio.brand_color else "#0a58d0"
        studio_email = studio.email if studio else None
        
        # Create reset token
        reset_token = AuthService.create_password_reset_token(
            email=request.email,
            user_type=user_type,
            user_id=str(user_id),
            studio_id=str(studio.id) if studio else ""
        )
        
        # Build reset URL
        reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"
        
        # Send email
        email_sent = EmailService.send_password_reset_email(
            to=request.email,
            user_name=user_name,
            reset_url=reset_url,
            studio_name=studio_name,
            studio_logo_url=studio_logo,
            brand_color=brand_color,
            reply_to=studio_email
        )
        
        if not email_sent and settings.smtp_enabled:
            logger.error(f"Failed to send password reset email to {request.email}")
        
        # In dev mode, log the reset URL
        if not settings.smtp_enabled:
            logger.info(f"[DEV MODE] Password reset URL for {request.email}: {reset_url}")
    
    # Always return success to prevent email enumeration
    return ForgotPasswordResponse(
        message="If an account with that email exists, we've sent password reset instructions."
    )


class AcceptInvitationRequest(BaseModel):
    """Request to accept an invitation."""
    token: str
    password: str


class AcceptInvitationResponse(BaseModel):
    """Response after accepting invitation."""
    message: str
    user_id: str
    email: str
    name: str


@router.post("/accept-invitation", response_model=AcceptInvitationResponse)
def accept_invitation(request: AcceptInvitationRequest, db: Session = Depends(get_db)):
    """
    Accept an invitation and set password.
    This endpoint allows invited users to set their password and activate their account.
    """
    from sqlalchemy import text
    
    # Find user by invitation token using raw SQL
    result = db.execute(
        text("SELECT id, email, name, invitation_accepted_at, password_hash FROM users WHERE invitation_token = :token"),
        {"token": request.token}
    )
    user = result.fetchone()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation token"
        )
    
    # Check if invitation already accepted
    if user.invitation_accepted_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has already been accepted"
        )
    
    # Check if user already has a password (shouldn't happen, but safety check)
    if user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account already has a password set"
        )
    
    # Set password and mark invitation as accepted via raw SQL (avoid model cache issues)
    from sqlalchemy import text
    hashed_password = AuthService.hash_password(request.password)
    
    db.execute(
        text("""
            UPDATE users 
            SET password_hash = :password_hash, 
                invitation_accepted_at = :accepted_at, 
                invitation_token = NULL, 
                email_verified = TRUE 
            WHERE id = :user_id
        """),
        {"password_hash": hashed_password, "accepted_at": datetime.utcnow(), "user_id": user.id}
    )
    
    db.commit()
    
    return AcceptInvitationResponse(
        message="Invitation accepted successfully. You can now log in.",
        user_id=user.id,
        email=user.email,
        name=user.name
    )


@router.get("/invitation/{token}")
def get_invitation_details(token: str, db: Session = Depends(get_db)):
    """
    Get details about an invitation (for the accept-invitation page).
    """
    from app.db.models import Studio
    from sqlalchemy import text
    
    # Use raw SQL to query by invitation_token (avoid model cache issues)
    result = db.execute(
        text("""
            SELECT u.id, u.email, u.name, u.role, u.studio_id, u.invitation_accepted_at,
                   s.name as studio_name, s.logo_url as studio_logo
            FROM users u
            LEFT JOIN studios s ON u.studio_id = s.id
            WHERE u.invitation_token = :token
        """),
        {"token": token}
    )
    row = result.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired invitation token"
        )
    
    if row.invitation_accepted_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has already been accepted"
        )
    
    return {
        "email": row.email,
        "name": row.name,
        "role": row.role,
        "studio_name": row.studio_name,
        "studio_logo": row.studio_logo,
    }


@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset password using a valid reset token.
    """
    # Verify token
    payload = AuthService.verify_password_reset_token(request.token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    user_type = payload.get("user_type")
    user_id = payload.get("sub")
    
    if not user_type or not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token payload"
        )
    
    # Reset the password
    success = AuthService.reset_password(db, user_type, user_id, request.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to reset password. User may not exist."
        )
    
    return ResetPasswordResponse(
        message="Password has been reset successfully. You can now log in with your new password."
    )
