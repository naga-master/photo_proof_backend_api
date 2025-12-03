"""Contract schemas for API requests and responses."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# Contract Template Schemas
class ContractTemplateBase(BaseModel):
    """Base contract template schema."""
    name: str = Field(..., max_length=255)
    category: Optional[str] = None
    content: str
    variables: Optional[Dict[str, Any]] = None
    is_active: bool = True


class ContractTemplateCreate(ContractTemplateBase):
    """Create contract template schema."""
    pass


class ContractTemplateUpdate(BaseModel):
    """Update contract template schema."""
    name: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = None
    content: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ContractTemplateResponse(ContractTemplateBase):
    """Contract template response schema."""
    id: str
    studio_id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Contract Schemas
class ContractBase(BaseModel):
    """Base contract schema."""
    title: str = Field(..., max_length=255)
    content: Optional[str] = None
    terms: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None


class ContractCreate(BaseModel):
    """Create contract schema."""
    client_id: int  # Client.id is Integer, not String
    project_id: Optional[str] = None
    template_id: Optional[str] = None
    title: str = Field(..., max_length=255)
    content: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    send_immediately: bool = False
    recipient_email: Optional[str] = None
    expires_days: int = Field(default=30, ge=1, le=365)


class ContractUpdate(BaseModel):
    """Update contract schema."""
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    terms: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None
    status: Optional[str] = None


class ContractResponse(BaseModel):
    """Contract response schema."""
    id: str
    studio_id: str
    client_id: int  # Client.id is Integer, not String
    project_id: Optional[str] = None
    template_id: Optional[str] = None
    contract_number: str
    title: str
    content: str
    terms: Optional[Dict[str, Any]] = None
    status: str
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    pdf_url: Optional[str] = None
    signed_pdf_url: Optional[str] = None
    # metadata field removed - SQLAlchemy conflict with table metadata
    created_at: datetime
    updated_at: datetime
    
    # Related data
    client_name: Optional[str] = None
    project_name: Optional[str] = None
    template_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ContractListResponse(BaseModel):
    """Contract list response."""
    contracts: List[ContractResponse]
    total: int
    offset: int
    limit: int


# Signature Schemas
class SignatureData(BaseModel):
    """Signature data schema."""
    signature: str = Field(..., description="Base64 encoded signature image")
    timestamp: Optional[datetime] = None
    agreement: bool = Field(..., description="User agreed to terms")


class SignContractRequest(BaseModel):
    """Sign contract request schema."""
    signature_data: SignatureData


class SignContractResponse(BaseModel):
    """Sign contract response schema."""
    status: str
    contract_id: str
    signed_at: datetime
    signature_hash: str


# Contract Activity Schemas
class ContractActivityResponse(BaseModel):
    """Contract activity response schema."""
    id: str
    contract_id: str
    action: str
    actor_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    activity_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Contract Stats
class ContractStats(BaseModel):
    """Contract statistics schema."""
    total: int
    draft: int
    pending: int
    signed: int
    expiring: int


# Email Template Schemas
class ContractEmailTemplateBase(BaseModel):
    """Base email template schema."""
    type: str = Field(..., max_length=50)
    subject: str = Field(..., max_length=255)
    body_html: str
    body_text: str
    variables: Optional[Dict[str, Any]] = None
    is_default: bool = False


class ContractEmailTemplateCreate(ContractEmailTemplateBase):
    """Create email template schema."""
    pass


class ContractEmailTemplateResponse(ContractEmailTemplateBase):
    """Email template response schema."""
    id: str
    studio_id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Contract verification
class VerifySignatureResponse(BaseModel):
    """Verify signature response."""
    contract_id: str
    signature_valid: bool
    verification_timestamp: datetime
    signed_at: Optional[datetime] = None
    signer_info: Optional[Dict[str, Any]] = None
