"""Service package and invoice models."""

from sqlalchemy import Column, String, Integer, ForeignKey, Text, Numeric, Date, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base, TimestampMixin


class ServicePackage(Base, TimestampMixin):
    """Photography service package/pricing tier."""

    __tablename__ = "service_packages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    studio_id = Column(String(36), ForeignKey("studios.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)  # 'Wedding', 'Corporate', 'Portraits', etc.
    description = Column(Text, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    
    # System vs custom packages
    is_predefined = Column(Boolean, nullable=False, default=False)
    
    # Features list stored as JSON array
    features = Column(JSON, nullable=False)  # ["6 Hours Coverage", "200 Photos", ...]
    
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Package Type and Restrictions (new columns for dynamic package system)
    package_type_id = Column(String(36), ForeignKey("package_types.id", ondelete="SET NULL"), nullable=True, index=True)
    restrictions = Column(JSON, nullable=True)  # Package-specific restrictions (photo limits, video limits, etc.)
    deliverables = Column(JSON, nullable=True)  # Structured deliverable specifications
    lifecycle_config = Column(JSON, nullable=True)  # Retention, archival, editing periods

    # Relationships
    studio = relationship("Studio", back_populates="service_packages")
    package_type = relationship("PackageType", back_populates="service_packages", foreign_keys=[package_type_id])
    projects = relationship("Project", back_populates="package")

    def __repr__(self):
        return f"<ServicePackage(id={self.id}, name={self.name}, price={self.price})>"


class Invoice(Base, TimestampMixin):
    """Invoice for projects and services."""

    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_number = Column(String(50), nullable=False, unique=True, index=True)
    
    studio_id = Column(String(36), ForeignKey("studios.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Dates
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    
    # Client info (denormalized for history preservation)
    client_name = Column(String(255), nullable=False)
    client_address = Column(Text, nullable=False)
    
    # Line items stored as JSON array of objects
    # Format: [{"id": "uuid", "description": "...", "quantity": 1, "unit_price": 100.00}, ...]
    items = Column(JSON, nullable=False)
    
    # Additional info
    notes = Column(Text, nullable=True)
    
    # Totals
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    
    # Status
    status = Column(String(50), nullable=False, default='Draft', index=True)
    # Statuses: 'Draft', 'Unpaid', 'Paid', 'Overdue'
    
    # Template used
    template = Column(String(50), nullable=False, default='modern')
    # Templates: 'modern', 'classic', 'minimalist'

    # Relationships
    studio = relationship("Studio", back_populates="invoices")
    client = relationship("Client")
    project = relationship("Project", back_populates="invoices")

    def __repr__(self):
        return f"<Invoice(id={self.id}, number={self.invoice_number}, status={self.status})>"
