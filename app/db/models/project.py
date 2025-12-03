"""Project and Folder models."""

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Date, Text, Numeric, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base, TimestampMixin


class Project(Base, TimestampMixin):
    """Project/Album entity - main container for photos."""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    studio_id = Column(String(36), ForeignKey("studios.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title = Column(String(500), nullable=False)
    shoot_date = Column(Date, nullable=True)
    cover_photo_id = Column(Integer, ForeignKey("photos.id", ondelete="SET NULL"), nullable=True)
    
    # Cached counts for performance
    photo_count = Column(Integer, nullable=False, default=0)
    total_comments = Column(Integer, nullable=False, default=0)
    
    # Gallery settings
    is_locked = Column(Boolean, nullable=False, default=False, index=True)
    layout = Column(String(50), nullable=False, default='layout1')
    
    # Financial info
    payment_status = Column(String(50), nullable=True)  # 'Paid', 'Unpaid', 'Due'
    price = Column(Numeric(10, 2), nullable=True)
    package_id = Column(String(36), ForeignKey("service_packages.id", ondelete="SET NULL"), nullable=True)
    
    # Project status
    status = Column(String(50), nullable=False, default='draft', index=True)
    # Statuses: 'draft', 'active', 'completed', 'archived'
    
    # Folder structure flag
    has_folders = Column(Boolean, nullable=False, default=False)
    
    # Package snapshot and usage tracking
    package_snapshot = Column(JSON, nullable=True)  # Frozen copy of package config at creation
    usage_stats = Column(JSON, nullable=True)  # Tracks usage vs limits
    
    # Gallery password protection
    is_password_protected = Column(Boolean, nullable=False, default=False)
    gallery_password = Column(String(255), nullable=True)  # Hashed password

    # Relationships
    studio = relationship("Studio", back_populates="projects")
    client = relationship("Client", back_populates="projects")
    package = relationship("ServicePackage", back_populates="projects")
    cover_photo = relationship("Photo", foreign_keys=[cover_photo_id], post_update=True)
    folders = relationship("Folder", back_populates="project", cascade="all, delete-orphan")
    photos = relationship("Photo", back_populates="project", foreign_keys="Photo.project_id", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="project")
    contracts = relationship("Contract", back_populates="project", cascade="all, delete-orphan")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, title={self.title}, client_id={self.client_id})>"


class Folder(Base, TimestampMixin):
    """Folder within a project for organizing photos."""

    __tablename__ = "folders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    cover_photo_id = Column(Integer, ForeignKey("photos.id", ondelete="SET NULL"), nullable=True)
    
    # Cached count
    photo_count = Column(Integer, nullable=False, default=0)
    
    # Ordering
    order_index = Column(Integer, nullable=False, default=0)

    # Relationships
    project = relationship("Project", back_populates="folders")
    cover_photo = relationship("Photo", foreign_keys=[cover_photo_id], post_update=True)
    photos = relationship("Photo", back_populates="folder", foreign_keys="Photo.folder_id", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Folder(id={self.id}, name={self.name}, project_id={self.project_id})>"
