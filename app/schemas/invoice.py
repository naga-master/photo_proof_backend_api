"""Invoice and service package schemas."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal


# ============================================================================
# SERVICE PACKAGE SCHEMAS
# ============================================================================

class ServicePackageFeature(BaseModel):
    """Service package feature item."""
    name: str
    included: bool
    details: Optional[str] = None


class ServicePackageBase(BaseModel):
    """Base service package fields."""
    name: str = Field(..., min_length=1, max_length=500)
    category: str = Field(..., min_length=1, max_length=100)  # Category (e.g., "Wedding", "Portrait")
    description: str = Field(default="", min_length=0)  # Allow empty description
    price: Decimal = Field(..., ge=0)


class ServicePackageCreate(ServicePackageBase):
    """Service package creation schema."""
    package_type_id: Optional[str] = None  # Reference to package type
    features: List[ServicePackageFeature] = []
    deliverables: List[str] = []
    restrictions: Optional[Dict[str, Any]] = None  # Package-specific restrictions
    lifecycle_config: Optional[Dict[str, Any]] = None  # Retention, archival, editing periods


class ServicePackageUpdate(BaseModel):
    """Service package update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0)
    package_type_id: Optional[str] = None
    features: Optional[List[ServicePackageFeature]] = None
    deliverables: Optional[List[str]] = None
    restrictions: Optional[Dict[str, Any]] = None
    lifecycle_config: Optional[Dict[str, Any]] = None


class ServicePackageResponse(ServicePackageBase):
    """Service package response schema."""
    id: str
    studio_id: str
    package_type_id: Optional[str] = None
    features: List[ServicePackageFeature]
    deliverables: Optional[List[str]] = []
    restrictions: Optional[Dict[str, Any]] = None
    lifecycle_config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ServicePackageListResponse(BaseModel):
    """List of service packages response."""
    packages: List[ServicePackageResponse]
    total: int


# ============================================================================
# INVOICE SCHEMAS
# ============================================================================

class InvoiceLineItem(BaseModel):
    """Invoice line item."""
    description: str
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    total: Decimal = Field(..., ge=0)


class InvoiceBase(BaseModel):
    """Base invoice fields."""
    invoice_number: str = Field(..., min_length=1)


class InvoiceCreate(BaseModel):
    """Invoice creation schema."""
    invoice_number: str = Field(..., min_length=1)
    project_id: int
    due_date: date
    line_items: List[InvoiceLineItem]
    notes: Optional[str] = None


class InvoiceUpdate(BaseModel):
    """Invoice update schema."""
    due_date: Optional[date] = None
    line_items: Optional[List[InvoiceLineItem]] = None
    notes: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(Draft|Sent|Paid|Overdue|Cancelled)$")


class InvoiceResponse(InvoiceBase):
    """Invoice response schema."""
    id: int
    studio_id: str
    project_id: int
    client_id: int
    invoice_date: date
    due_date: date
    line_items: List[InvoiceLineItem]
    subtotal: Decimal
    tax: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    is_overdue: bool = False
    days_overdue: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class InvoiceListResponse(BaseModel):
    """List of invoices response."""
    invoices: List[InvoiceResponse]
    total: int


# ============================================================================
# PAYMENT SCHEMAS
# ============================================================================

class PaymentRequest(BaseModel):
    """Payment recording request."""
    invoice_id: int
    amount: Decimal = Field(..., gt=0)
    payment_method: str = Field(..., pattern="^(Cash|Check|Credit Card|Bank Transfer|PayPal|Stripe)$")
    payment_date: Optional[date] = None
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    """Payment response."""
    invoice_id: int
    amount_paid: Decimal
    balance_due: Decimal
    status: str
    payment_date: date
