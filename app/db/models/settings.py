"""Layout templates and communication settings models."""

from sqlalchemy import Column, String, ForeignKey, Boolean, Text, JSON
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class LayoutTemplate(Base):
    """Gallery layout template (predefined options)."""

    __tablename__ = "layout_templates"

    id = Column(String(50), primary_key=True)  # 'layout1', 'layout2', ..., 'layout9'
    
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=False)
    
    # Layout configuration
    header = Column(String(50), nullable=False)  # 'Cover' or 'Title Only'
    grid = Column(String(50), nullable=False)  # 'Masonry', 'Grid', 'Stacked'
    aspect = Column(String(50), nullable=False)  # 'Portrait' or 'Landscape'
    theme = Column(String(50), nullable=False)  # 'White', 'Gray', 'Cream', 'Black'
    
    is_predefined = Column(Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<LayoutTemplate(id={self.id}, name={self.name})>"


class CommunicationSettings(Base, TimestampMixin):
    """Studio communication settings for email and WhatsApp."""

    __tablename__ = "communication_settings"

    id = Column(String(36), primary_key=True)  # Same as studio_id for one-to-one
    studio_id = Column(String(36), ForeignKey("studios.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Email settings
    email_from_address = Column(String(255), nullable=True)
    email_from_name = Column(String(255), nullable=True)
    email_api_key = Column(Text, nullable=True)  # Should be encrypted in production
    
    # WhatsApp settings
    whatsapp_phone_number_id = Column(String(255), nullable=True)
    whatsapp_business_account_id = Column(String(255), nullable=True)
    whatsapp_access_token = Column(Text, nullable=True)  # Should be encrypted in production

    # Relationships
    studio = relationship("Studio", back_populates="communication_settings")

    def __repr__(self):
        return f"<CommunicationSettings(studio_id={self.studio_id})>"
