"""Authentication service with JWT token management."""

import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Tuple, Union
import bcrypt
from jose import JWTError, jwt
import os
from dotenv import load_dotenv

load_dotenv()
from sqlalchemy.orm import Session

from app.db.models import Studio, User, Client
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    TokenResponse,
    StudioResponse,
    UserResponse,
    ClientResponse,
)


# Configuration from environment
SECRET_KEY = os.getenv("SECRET_KEY", "YOUR_SECRET_KEY_HERE")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))  # Short-lived: 30 minutes
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))  # 7 days


class AuthService:
    """Authentication service."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        # Truncate to 72 bytes (bcrypt limit)
        password_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash using bcrypt."""
        # Truncate to 72 bytes (bcrypt limit)
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    
    @staticmethod
    def generate_password(length: int = 8) -> str:
        """Generate a random password for client gallery access."""
        # Use letters and digits for easy sharing (no confusing chars like 0/O, l/1)
        chars = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789'
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token with longer expiration."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """Decode and validate JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            return None
    
    @staticmethod
    def verify_refresh_token(token: str) -> Optional[dict]:
        """Verify refresh token and return payload if valid."""
        payload = AuthService.decode_token(token)
        if not payload or payload.get("type") != "refresh":
            return None
        return payload
    
    @staticmethod
    def studio_login(db: Session, login_data: LoginRequest) -> Optional[Tuple[User, str]]:
        """Authenticate studio user and return user + token."""
        # Studio users are in the User table with role='studio_owner'
        user = db.query(User).filter(
            User.username == login_data.username,
            User.role == "studio_owner"
        ).first()
        
        if not user or not user.password_hash:
            return None
            
        if not AuthService.verify_password(login_data.password, user.password_hash):
            return None
        
        # Get the studio associated with this user
        studio = db.query(Studio).filter(Studio.id == user.studio_id).first()
        
        # Create token
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role,
            "studio_id": user.studio_id,
        }
        access_token = AuthService.create_access_token(token_data)
        
        return user, access_token
    
    @staticmethod
    def client_login(db: Session, login_data: LoginRequest) -> Optional[Tuple[Union[User, Client], str]]:
        """Authenticate client and return client + token.
        
        Uses Client.password directly for simple gallery access authentication.
        Falls back to User table for legacy accounts.
        """
        # First, try direct Client authentication (new simple method)
        client = db.query(Client).filter(
            Client.email == login_data.username
        ).first()
        
        if client and client.password:
            # Client has direct password - use it
            if AuthService.verify_password(login_data.password, client.password):
                # Create token with client info
                token_data = {
                    "sub": f"client_{client.id}",
                    "email": client.email,
                    "role": "client",
                    "studio_id": client.studio_id,
                    "client_id": client.id
                }
                access_token = AuthService.create_access_token(token_data)
                return client, access_token
        
        # Fallback: Try legacy User table authentication
        user = db.query(User).filter(
            User.username == login_data.username,
            User.role == "client"
        ).first()
        
        if not user or not user.password_hash:
            return None
            
        if not AuthService.verify_password(login_data.password, user.password_hash):
            return None
        
        # Get the client record associated with this user
        client = db.query(Client).filter(Client.user_id == user.id).first()
        
        # Create token
        token_data = {
            "sub": user.id,
            "email": user.email,
            "role": user.role,
            "studio_id": user.studio_id,
            "client_id": client.id if client else None
        }
        access_token = AuthService.create_access_token(token_data)
        
        return user, access_token
    
    @staticmethod
    def register_studio(db: Session, register_data: RegisterRequest) -> Tuple[Studio, str]:
        """Register new studio account."""
        # Check if email exists
        existing = db.query(Studio).filter(Studio.email == register_data.email).first()
        if existing:
            raise ValueError("Email already registered")
        
        # Create studio
        studio = Studio(
            id=f"studio_{secrets.token_urlsafe(8)}",
            studio_name=register_data.name,
            email=register_data.email,
            password_hash=AuthService.hash_password(register_data.password),
            logo="/path/to/default/logo.png",
        )
        
        db.add(studio)
        db.commit()
        db.refresh(studio)
        
        # Create token
        token_data = {
            "sub": studio.id,
            "email": studio.email,
            "role": "studio",
            "studio_name": studio.studio_name,
        }
        access_token = AuthService.create_access_token(token_data)
        
        return studio, access_token
    
    @staticmethod
    def get_current_user(db: Session, token: str) -> Optional[dict]:
        """Get current user from token."""
        payload = AuthService.decode_token(token)
        
        if not payload:
            return None
        
        user_id = payload.get("sub")
        role = payload.get("role")
        
        if not user_id or not role:
            return None
        
        # Fetch user based on role
        if role == "studio":
            studio = db.query(Studio).filter(Studio.id == user_id).first()
            if studio:
                return {
                    "id": studio.id,
                    "email": studio.email,
                    "role": "studio",
                    "studio_name": studio.studio_name,
                    "entity": studio,
                }
        
        elif role == "client":
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                client = db.query(Client).filter(Client.user_id == user.id).first()
                return {
                    "id": user.id,
                    "email": user.email,
                    "role": "client",
                    "client_id": client.id if client else None,
                    "studio_id": user.studio_id,
                    "entity": user,
                }
        
        return None
