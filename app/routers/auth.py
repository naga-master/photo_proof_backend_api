"""Authentication router."""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    StudioResponse,
    ClientResponse,
)


router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/studio/login", response_model=LoginResponse)
def studio_login(login_data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Studio user login with httpOnly cookie support."""
    result = AuthService.studio_login(db, login_data)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    user, access_token = result
    
    # Create refresh token
    token_data = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "studio_id": user.studio_id,
    }
    refresh_token = AuthService.create_refresh_token(token_data)
    
    # Set httpOnly cookies for better security
    # Access token - short lived
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=30 * 60  # 30 minutes
    )
    
    # Refresh token - longer lived
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    return LoginResponse(
        token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/client/login", response_model=LoginResponse)
def client_login(login_data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Client user login with httpOnly cookie support."""
    result = AuthService.client_login(db, login_data)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    user, access_token = result
    
    # Get client record
    from app.db.models import Client
    client = db.query(Client).filter(Client.user_id == user.id).first()
    
    # Create refresh token
    token_data = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "studio_id": user.studio_id,
        "client_id": client.id if client else None
    }
    refresh_token = AuthService.create_refresh_token(token_data)
    
    # Set httpOnly cookies for better security
    # Access token - short lived
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=30 * 60  # 30 minutes
    )
    
    # Refresh token - longer lived
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    return LoginResponse(
        token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
        client_id=client.id if client else None
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


@router.get("/me")
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user."""
    token = credentials.credentials
    user_data = AuthService.get_current_user(db, token)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return user_data


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token from cookie or Authorization header."""
    # Try to get refresh token from cookie first, then from Authorization header
    token = refresh_token
    if not token and credentials:
        token = credentials.credentials
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided"
        )
    
    # Verify refresh token
    payload = AuthService.verify_refresh_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Fetch user from database to ensure they still exist and are active
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
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=30 * 60  # 30 minutes
    )
    
    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer"
    )


@router.post("/logout")
def logout(response: Response):
    """Logout user by clearing authentication cookies."""
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return {"message": "Successfully logged out"}
