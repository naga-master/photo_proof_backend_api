"""Authentication router."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

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
def studio_login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Studio user login."""
    result = AuthService.studio_login(db, login_data)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    user, access_token = result
    
    return LoginResponse(
        token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/client/login", response_model=LoginResponse)
def client_login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Client user login."""
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
    
    return LoginResponse(
        token=access_token,
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
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Refresh access token."""
    token = credentials.credentials
    user_data = AuthService.get_current_user(db, token)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Generate new token
    token_data = {
        "sub": user_data["id"],
        "email": user_data["email"],
        "role": user_data["role"],
    }
    
    if user_data["role"] == "studio":
        token_data["studio_name"] = user_data.get("studio_name")
    elif user_data["role"] == "client":
        token_data["client_id"] = user_data.get("client_id")
        token_data["studio_id"] = user_data.get("studio_id")
    
    new_token = AuthService.create_access_token(token_data)
    
    return TokenResponse(
        access_token=new_token,
        token_type="bearer"
    )
