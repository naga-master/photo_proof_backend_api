"""Invoice and payment schemas."""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

from app.schemas.enums import UserRole


class InvoiceStatus(str):
    """Invoice status enum values."""
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class InvoiceItem(BaseModel):
    """Individual invoice line item."""
    id: str
    description: str
    quantity: int
    unit_price: Decimal
    total: Decimal
    category: Optional[str] = None


class InvoicePayment(BaseModel):
    """Payment record for an invoice."""
    id: str
    amount: Decimal
    payment_method: str
    transaction_id: Optional[str] = None
    payment_date: datetime
    notes: Optional[str] = None


class InvoiceRead(BaseModel):
    """Invoice read schema."""
    id: str
    invoice_number: str
    client_id: str
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    project_id: Optional[str] = None
    studio_id: str
    status: str
    issue_date: date
    due_date: date
    items: List[InvoiceItem] = []
    subtotal: Decimal
    tax_rate: Decimal = Decimal("0.00")
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Optional[Decimal] = Decimal("0.00")
    outstanding_amount: Optional[Decimal] = None
    currency: str = "USD"
    payments: Optional[List[InvoicePayment]] = []
    notes: Optional[str] = None
    terms: Optional[str] = None
    payment_terms: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Alias for backward compatibility
Invoice = InvoiceRead


class InvoiceRequest(BaseModel):
    """Request to create an invoice."""
    client_id: str
    project_id: Optional[str] = None
    issue_date: Optional[date] = None
    due_date: date
    items: List[InvoiceItem]
    tax_rate: Optional[Decimal] = Decimal("0.00")
    currency: Optional[str] = "USD"
    notes: Optional[str] = None
    payment_terms: Optional[str] = None


class InvoiceUpdate(BaseModel):
    """Request to update an invoice."""
    status: Optional[str] = None
    due_date: Optional[date] = None
    items: Optional[List[InvoiceItem]] = None
    tax_rate: Optional[Decimal] = None
    notes: Optional[str] = None
    payment_terms: Optional[str] = None


class PaymentRequest(BaseModel):
    """Payment processing request."""
    amount: Decimal
    currency: str = "USD"
    payment_method: str


class PaymentResponse(BaseModel):
    """Payment processing response."""
    payment_id: str
    invoice_id: str
    amount: Decimal
    currency: str
    payment_method: str
    status: str
    transaction_id: Optional[str] = None
    processed_at: datetime
    fees: Optional[Decimal] = None
    net_amount: Optional[Decimal] = None


class RecurringInvoiceConfig(BaseModel):
    """Recurring invoice configuration."""
    client_id: str
    frequency: str  # monthly, quarterly, yearly
    start_date: date
    template_data: Dict[str, Any]
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    outstanding_amount: Decimal
    payments: List[InvoicePayment]
    notes: Optional[str] = None
    terms: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CreateInvoiceRequest(BaseModel):
    """Request to create an invoice."""
    client_id: str
    issue_date: date
    due_date: date
    items: List[Dict[str, Any]]  # Will be converted to InvoiceItem
    tax_rate: Decimal = Decimal("0.00")
    notes: Optional[str] = None
    terms: Optional[str] = None


class UpdateInvoiceRequest(BaseModel):
    """Request to update an invoice."""
    status: Optional[str] = None
    due_date: Optional[date] = None
    items: Optional[List[Dict[str, Any]]] = None
    tax_rate: Optional[Decimal] = None
    notes: Optional[str] = None
    terms: Optional[str] = None


class RecordPaymentRequest(BaseModel):
    """Request to record a payment."""
    amount: Decimal
    payment_method: str
    transaction_id: Optional[str] = None
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None


class InvoiceListResponse(BaseModel):
    """Response for invoice list."""
    invoices: List[InvoiceRead]
    total_count: int
    total_outstanding: Decimal


class InvoiceStats(BaseModel):
    """Invoice statistics."""
    total_invoiced: Decimal
    total_paid: Decimal
    total_outstanding: Decimal
    overdue_count: int
    recent_payments: List[InvoicePayment]