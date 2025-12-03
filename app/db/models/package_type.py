"""Package Type model for dynamic package system."""

from sqlalchemy import Column, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
import uuid

from .base import Base, TimestampMixin


class PackageType(Base, TimestampMixin):
    """Package Type entity - defines different photography package categories with dynamic schemas."""

    __tablename__ = "package_types"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    
    # Type classification
    is_predefined = Column(Boolean, nullable=False, default=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Dynamic form schema stored as JSON
    # Structure: {"sections": [{"title": "...", "fields": [...]}]}
    attribute_schema = Column(Text, nullable=False)  # JSON stored as text
    
    # Creator tracking
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    service_packages = relationship(
        "ServicePackage",
        back_populates="package_type",
        foreign_keys="[ServicePackage.package_type_id]"
    )

    def __repr__(self):
        return f"<PackageType(id={self.id}, name={self.name}, display_name={self.display_name})>"
