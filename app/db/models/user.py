"""User, Studio, and Client models."""

from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text, Integer, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base, TimestampMixin


class Studio(Base, TimestampMixin):
    """Photography studio/business entity."""

    __tablename__ = "studios"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    
    # Multi-tenant fields
    subdomain = Column(String(100), unique=True, nullable=True, index=True)
    # Example: 'mystudio' for mystudio.photoapp.com
    
    # Branding
    logo_url = Column(String(500), nullable=True)
    brand_color = Column(String(7), nullable=False, default='#1e293b')  # Hex color
    typography = Column(String(255), nullable=False, default='System Default (Inter & Cormorant)')
    default_layout_id = Column(String(50), nullable=False, default='layout1')
    default_template_id = Column(String(50), nullable=False, default='modern')
    studio_photo = Column(String(500), nullable=True)
    studio_description = Column(Text, nullable=True)
    studio_display_image = Column(String(500), nullable=True)
    custom_css = Column(Text, nullable=True)  # Custom CSS for white-labeling
    
    # Subscription (legacy - will be replaced by StudioSubscription)
    subscription_tier = Column(String(50), nullable=False, default='free')
    subscription_status = Column(String(50), nullable=False, default='trial')
    max_projects = Column(Integer, nullable=False, default=5)
    max_storage_gb = Column(Integer, nullable=False, default=10)
    storage_used_bytes = Column(Integer, nullable=False, default=0)
    
    # Onboarding status
    onboarding_completed = Column(Boolean, nullable=False, default=False)
    onboarding_step = Column(String(50), nullable=True)
    # Steps: 'registration', 'plan', 'domain', 'branding', 'payment', 'completed'
    
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Relationships
    users = relationship("User", back_populates="studio", cascade="all, delete-orphan")
    clients = relationship("Client", back_populates="studio", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="studio", cascade="all, delete-orphan")
    service_packages = relationship("ServicePackage", back_populates="studio", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="studio", cascade="all, delete-orphan")
    communication_settings = relationship("CommunicationSettings", back_populates="studio", uselist=False)
    
    # Multi-tenant relationships
    domains = relationship("StudioDomain", back_populates="studio", cascade="all, delete-orphan")
    subscription = relationship("StudioSubscription", back_populates="studio", uselist=False)
    features = relationship("StudioFeature", back_populates="studio", cascade="all, delete-orphan")
    usage_stats = relationship("StudioUsageStats", back_populates="studio", cascade="all, delete-orphan")
    
    # Contract relationships
    contract_templates = relationship("ContractTemplate", back_populates="studio", cascade="all, delete-orphan")
    contracts = relationship("Contract", back_populates="studio", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Studio(id={self.id}, name={self.name})>"


class User(Base, TimestampMixin):
    """Application user - can be studio owner, studio staff, or client."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    studio_id = Column(String(36), ForeignKey("studios.id", ondelete="CASCADE"), nullable=True, index=True)
    
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    username = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for social auth
    
    role = Column(String(50), nullable=False, default='client', index=True)
    # Roles: 'studio_owner', 'studio_admin', 'studio_photographer', 'client'
    
    permissions = Column(JSON, nullable=True, default={})  # RBAC permissions
    
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    email_verified = Column(Boolean, nullable=False, default=False)
    last_login_at = Column(DateTime, nullable=True)

    # Relationships
    studio = relationship("Studio", back_populates="users")
    client_profile = relationship("Client", back_populates="user", uselist=False)
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    uploaded_photos = relationship("Photo", back_populates="uploaded_by_user", foreign_keys="Photo.uploaded_by")
    favorites = relationship("UserPhotoFavorite", back_populates="user", cascade="all, delete-orphan")
    selections = relationship("UserPhotoSelection", back_populates="user", cascade="all, delete-orphan")
    
    # Consent relationships
    consents = relationship("UserConsent", back_populates="user", cascade="all, delete-orphan")
    data_exports = relationship("DataExportRequest", back_populates="user", cascade="all, delete-orphan")
    deletion_requests = relationship("AccountDeletionRequest", back_populates="user", cascade="all, delete-orphan")
    
    # Project assignment relationship
    project_memberships = relationship("ProjectMember", foreign_keys="ProjectMember.user_id", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class Client(Base, TimestampMixin):
    """Client/customer entity - can optionally be linked to a User account."""

    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    studio_id = Column(String(36), ForeignKey("studios.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True, index=True)
    
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    username = Column(String(255), nullable=True, unique=True, index=True)  # For client login
    password = Column(String(255), nullable=True)  # Direct client login (hashed)
    
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    profile_picture = Column(String(500), nullable=True)
    
    # Communication preferences
    whatsapp_opt_in = Column(Boolean, nullable=False, default=False)
    email_opt_in = Column(Boolean, nullable=False, default=True)
    
    last_activity = Column(String(255), nullable=True)  # Human-readable: "Commented 2 days ago"
    
    status = Column(String(50), nullable=False, default='active', index=True)
    # Statuses: 'active', 'inactive', 'archived'

    # Relationships
    studio = relationship("Studio", back_populates="clients")
    user = relationship("User", back_populates="client_profile")
    projects = relationship("Project", back_populates="client", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="client", cascade="all, delete-orphan")
    contracts = relationship("Contract", back_populates="client", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Client(id={self.id}, name={self.name}, email={self.email})>"
