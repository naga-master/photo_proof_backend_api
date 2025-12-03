"""Authentication and user schemas."""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


# ============================================================================
# AUTH SCHEMAS
# ============================================================================

class LoginRequest(BaseModel):
    """Login request - works for both studio users and clients."""
    username: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6, max_length=255)


class LoginResponse(BaseModel):
    """Login response with token and user info."""
    token: str
    refresh_token: Optional[str] = None
    user: "UserResponse"
    client_id: Optional[int] = None  # Set if user is a client
    
    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    """User registration request."""
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6, max_length=255)
    role: str = Field(default="client", pattern="^(studio_owner|studio_admin|studio_photographer|client)$")
    studio_id: Optional[str] = None  # Required for non-client roles


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token: Optional[str] = None  # Backwards compatibility - same as access_token
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    """Request to initiate password reset."""
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    """Response for forgot password request."""
    message: str


class ResetPasswordRequest(BaseModel):
    """Request to reset password with token."""
    token: str
    new_password: str = Field(..., min_length=6, max_length=255)


class ResetPasswordResponse(BaseModel):
    """Response for password reset."""
    message: str


# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    """Base user fields."""
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=255)
    role: str = Field(default="client")
    phone: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=6)
    studio_id: Optional[str] = None


class UserUpdate(BaseModel):
    """User update schema."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    """User response schema."""
    id: str
    studio_id: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    email_verified: bool
    permissions: Optional[dict] = None  # RBAC permissions
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# STUDIO SCHEMAS
# ============================================================================

class StudioBase(BaseModel):
    """Base studio fields."""
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None


class StudioCreate(StudioBase):
    """Studio creation schema."""
    password: str = Field(..., min_length=6)  # For creating owner account


class StudioUpdate(BaseModel):
    """Studio update schema."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None
    brand_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    typography: Optional[str] = None
    default_layout_id: Optional[str] = None
    default_template_id: Optional[str] = None
    studio_photo: Optional[str] = None
    studio_description: Optional[str] = None
    studio_display_image: Optional[str] = None


class StudioResponse(StudioBase):
    """Studio response schema."""
    id: str
    logo_url: Optional[str] = None
    brand_color: str
    typography: str
    default_layout_id: str
    default_template_id: str
    studio_photo: Optional[str] = None
    studio_description: Optional[str] = None
    studio_display_image: Optional[str] = None
    subscription_tier: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# CLIENT SCHEMAS
# ============================================================================

class ClientBase(BaseModel):
    """Base client fields."""
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None


class ClientCreate(ClientBase):
    """Client creation schema."""
    username: Optional[str] = Field(None, min_length=3, max_length=255)
    password: Optional[str] = Field(None, min_length=6)  # Optional for client login
    whatsapp_opt_in: bool = False
    email_opt_in: bool = True


class ClientUpdate(BaseModel):
    """Client update schema."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    avatar_url: Optional[str] = None
    profile_picture: Optional[str] = None
    whatsapp_opt_in: Optional[bool] = None
    email_opt_in: Optional[bool] = None


class ClientResponse(ClientBase):
    """Client response schema."""
    id: int
    studio_id: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None  # Plain password (only returned during creation/reset)
    has_password: bool = False  # Indicates if client has a password set
    avatar_url: Optional[str] = None
    profile_picture: Optional[str] = None
    whatsapp_opt_in: bool
    email_opt_in: bool
    last_activity: Optional[str] = None
    status: str
    total_projects: int = 0  # Computed field for project count
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
