"""Invoices router for invoice management."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from datetime import datetime, date
import uuid

from app.db.session import get_db
from app.db.models import Invoice, User, Client, Project
from app.api.deps import get_current_user
from app.core.permissions import (
    require_view_invoices,
    require_create_invoices,
    require_edit_invoices,
    require_delete_invoices,
)


router = APIRouter()


# Request/Response schemas
class InvoiceItem(BaseModel):
    """Invoice line item."""
    id: str = ""
    description: str
    quantity: int = 1
    unit_price: Decimal


class InvoiceCreate(BaseModel):
    """Create invoice."""
    client_id: int
    project_id: Optional[int] = None
    invoice_date: date
    due_date: date
    items: List[InvoiceItem]
    notes: Optional[str] = None
    tax_rate: Decimal = Decimal("0.08")
    template: str = "modern"


class InvoiceUpdate(BaseModel):
    """Update invoice."""
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    items: Optional[List[InvoiceItem]] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    template: Optional[str] = None


class InvoiceResponse(BaseModel):
    """Invoice response."""
    id: str
    invoice_number: str
    studio_id: str
    client_id: Optional[int] = None
    project_id: Optional[int] = None
    invoice_date: date
    due_date: date
    client_name: str
    client_address: str
    items: list
    notes: Optional[str] = None
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    status: str
    template: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


@router.get("/", response_model=List[InvoiceResponse])
def list_invoices(
    client_id: Optional[int] = Query(None, description="Filter by client"),
    status_filter: Optional[str] = Query(None, description="Filter by status: Draft, Unpaid, Paid, Overdue"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Invoice]:
    """
    List all invoices for the current studio.
    
    Only studio users can access this endpoint.
    """
    # Only studio users can list invoices
    if not current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can list invoices"
        )
    
    query = db.query(Invoice).filter(Invoice.studio_id == current_user.studio_id)
    
    if client_id:
        query = query.filter(Invoice.client_id == client_id)
    
    if status_filter:
        query = query.filter(Invoice.status == status_filter)
    
    invoices = (
        query
        .order_by(Invoice.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return invoices


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Invoice:
    """
    Get a specific invoice by ID.
    
    Studio users can access any invoice in their studio.
    Clients can access their own invoices.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Check access permissions
    if current_user.studio_id == invoice.studio_id:
        return invoice
    
    # Clients can access their invoices
    if current_user.client_profile and invoice.client_id == current_user.client_profile.id:
        return invoice
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to access this invoice"
    )


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Invoice:
    """
    Create a new invoice.
    
    Only studio users can create invoices.
    """
    # Only studio users can create invoices
    if not current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can create invoices"
        )
    
    # Verify client exists and belongs to studio
    client = (
        db.query(Client)
        .filter(
            Client.id == invoice_data.client_id,
            Client.studio_id == current_user.studio_id
        )
        .first()
    )
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found or doesn't belong to your studio"
        )
    
    # Verify project if provided
    if invoice_data.project_id:
        project = (
            db.query(Project)
            .filter(
                Project.id == invoice_data.project_id,
                Project.studio_id == current_user.studio_id
            )
            .first()
        )
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
    
    # Generate invoice number
    invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
    
    # Process items and calculate totals
    processed_items = []
    subtotal = Decimal("0.00")
    
    for item in invoice_data.items:
        item_id = item.id or str(uuid.uuid4())
        item_total = item.quantity * item.unit_price
        
        processed_items.append({
            "id": item_id,
            "description": item.description,
            "quantity": item.quantity,
            "unit_price": float(item.unit_price),
            "total": float(item_total),
        })
        
        subtotal += item_total
    
    # Calculate tax and total
    tax = subtotal * invoice_data.tax_rate
    total = subtotal + tax
    
    # Create invoice
    invoice = Invoice(
        invoice_number=invoice_number,
        studio_id=current_user.studio_id,
        client_id=client.id,
        project_id=invoice_data.project_id,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        client_name=client.name,
        client_address=client.address or "",
        items=processed_items,
        notes=invoice_data.notes,
        subtotal=subtotal,
        tax=tax,
        total=total,
        status="Draft",
        template=invoice_data.template,
    )
    
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    
    return invoice


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    invoice_id: str,
    invoice_update: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Invoice:
    """
    Update an invoice.
    
    Only studio users can update invoices.
    Only Draft invoices can be fully edited.
    """
    # Only studio users can update
    if not current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can update invoices"
        )
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Check studio ownership
    if invoice.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this invoice"
        )
    
    update_data = invoice_update.model_dump(exclude_unset=True)
    
    # If updating items, recalculate totals
    if "items" in update_data:
        if invoice.status != "Draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only modify items on Draft invoices"
            )
        
        processed_items = []
        subtotal = Decimal("0.00")
        
        for item in update_data["items"]:
            item_id = item.get("id") or str(uuid.uuid4())
            quantity = item["quantity"]
            unit_price = Decimal(str(item["unit_price"]))
            item_total = quantity * unit_price
            
            processed_items.append({
                "id": item_id,
                "description": item["description"],
                "quantity": quantity,
                "unit_price": float(unit_price),
                "total": float(item_total),
            })
            
            subtotal += item_total
        
        tax_rate = Decimal("0.08")  # Should be configurable
        tax = subtotal * tax_rate
        total = subtotal + tax
        
        invoice.items = processed_items
        invoice.subtotal = subtotal
        invoice.tax = tax
        invoice.total = total
        
        del update_data["items"]
    
    # Apply other updates
    for field, value in update_data.items():
        setattr(invoice, field, value)
    
    db.commit()
    db.refresh(invoice)
    
    return invoice


@router.patch("/{invoice_id}/send", response_model=InvoiceResponse)
def send_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Invoice:
    """
    Send invoice to client (marks as Unpaid).
    
    Only studio users can send invoices.
    """
    if not current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can send invoices"
        )
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    if invoice.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    if invoice.status != "Draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Draft invoices can be sent"
        )
    
    invoice.status = "Unpaid"
    db.commit()
    db.refresh(invoice)
    
    # TODO: Send email notification to client
    
    return invoice


@router.patch("/{invoice_id}/pay", response_model=InvoiceResponse)
def mark_invoice_paid(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Invoice:
    """
    Mark invoice as paid.
    
    Only studio users can mark invoices as paid.
    """
    if not current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can mark invoices as paid"
        )
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    if invoice.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    invoice.status = "Paid"
    db.commit()
    db.refresh(invoice)
    
    return invoice


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete an invoice.
    
    Only studio users can delete invoices.
    Only Draft invoices can be deleted.
    """
    if not current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can delete invoices"
        )
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    if invoice.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    if invoice.status != "Draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Draft invoices can be deleted"
        )
    
    db.delete(invoice)
    db.commit()
