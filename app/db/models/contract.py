"""Contract management database models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


def _uuid() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())


ContractStatus = Enum(
    "draft",
    "sent", 
    "viewed",
    "signed",
    "expired",
    "cancelled",
    name="contract_status_enum"
)

ContractCategory = Enum(
    "wedding",
    "portrait",
    "commercial",
    "event",
    "other",
    name="contract_category_enum"
)


class ContractTemplate(Base):
    """Contract template model."""
    __tablename__ = "contract_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    studio_id: Mapped[str] = mapped_column(ForeignKey("studios.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(ContractCategory, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    studio: Mapped["Studio"] = relationship("Studio", back_populates="contract_templates")
    contracts: Mapped[list["Contract"]] = relationship("Contract", back_populates="template")


class Contract(Base):
    """Contract model."""
    __tablename__ = "contracts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    studio_id: Mapped[str] = mapped_column(ForeignKey("studios.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    template_id: Mapped[str | None] = mapped_column(ForeignKey("contract_templates.id", ondelete="SET NULL"), nullable=True)
    
    # Contract details
    contract_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    terms: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(ContractStatus, default="draft", index=True)
    
    # Dates
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Signature data
    client_signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_signature_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)
    client_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    client_user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # PDF storage
    pdf_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    signed_pdf_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Metadata (using contract_metadata to avoid SQLAlchemy reserved keyword)
    contract_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    studio: Mapped["Studio"] = relationship("Studio", back_populates="contracts")
    client: Mapped["Client"] = relationship("Client", back_populates="contracts")
    project: Mapped["Project"] = relationship("Project", back_populates="contracts")
    template: Mapped[ContractTemplate | None] = relationship("ContractTemplate", back_populates="contracts")
    activities: Mapped[list["ContractActivity"]] = relationship("ContractActivity", back_populates="contract", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Contract {self.contract_number}: {self.title}>"


class ContractActivity(Base):
    """Contract activity log model."""
    __tablename__ = "contract_activities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    activity_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    contract: Mapped[Contract] = relationship("Contract", back_populates="activities")
    actor: Mapped["User"] = relationship("User")


class ContractEmailTemplate(Base):
    """Email templates for contract notifications."""
    __tablename__ = "contract_email_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    studio_id: Mapped[str] = mapped_column(ForeignKey("studios.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body_html: Mapped[str] = mapped_column(Text, nullable=False)
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    studio: Mapped["Studio"] = relationship("Studio")
