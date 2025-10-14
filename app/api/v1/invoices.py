"""Invoice management API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.invoices import (
    InvoiceRead,
    CreateInvoiceRequest,
    UpdateInvoiceRequest,
    RecordPaymentRequest,
    InvoiceListResponse,
    InvoiceStats,
)
from app.schemas.users import UserRead
from app.services.invoice_service import InvoiceService


router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])


@router.get("/", response_model=InvoiceListResponse)
async def get_invoices(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    client_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get all invoices for the studio."""
    service = InvoiceService(db)
    invoices, total_count = await service.get_studio_invoices(
        current_user.studio_id, skip, limit, status_filter, client_id
    )
    
    total_outstanding = await service.get_total_outstanding(current_user.studio_id)
    
    return InvoiceListResponse(
        invoices=invoices,
        total_count=total_count,
        total_outstanding=total_outstanding,
    )


@router.post("/", response_model=InvoiceRead)
async def create_invoice(
    request: CreateInvoiceRequest,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Create a new invoice."""
    service = InvoiceService(db)
    return await service.create_invoice(current_user.studio_id, request)


@router.get("/stats", response_model=InvoiceStats)
async def get_invoice_stats(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get invoice statistics for the studio."""
    service = InvoiceService(db)
    return await service.get_invoice_stats(current_user.studio_id)


@router.get("/{invoice_id}", response_model=InvoiceRead)
async def get_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Get a specific invoice."""
    service = InvoiceService(db)
    invoice = await service.get_invoice(invoice_id)
    
    if not invoice or invoice.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    return invoice


@router.put("/{invoice_id}", response_model=InvoiceRead)
async def update_invoice(
    invoice_id: str,
    request: UpdateInvoiceRequest,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Update an invoice."""
    service = InvoiceService(db)
    invoice = await service.get_invoice(invoice_id)
    
    if not invoice or invoice.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    return await service.update_invoice(invoice_id, request)


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Delete an invoice."""
    service = InvoiceService(db)
    invoice = await service.get_invoice(invoice_id)
    
    if not invoice or invoice.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    await service.delete_invoice(invoice_id)
    return {"message": "Invoice deleted successfully"}


@router.post("/{invoice_id}/send")
async def send_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Send an invoice to the client."""
    service = InvoiceService(db)
    invoice = await service.get_invoice(invoice_id)
    
    if not invoice or invoice.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    await service.send_invoice(invoice_id)
    return {"message": "Invoice sent successfully"}


@router.post("/{invoice_id}/payments", response_model=InvoiceRead)
async def record_payment(
    invoice_id: str,
    request: RecordPaymentRequest,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Record a payment for an invoice."""
    service = InvoiceService(db)
    invoice = await service.get_invoice(invoice_id)
    
    if not invoice or invoice.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    return await service.record_payment(invoice_id, request)


@router.get("/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
):
    """Generate and download invoice PDF."""
    service = InvoiceService(db)
    invoice = await service.get_invoice(invoice_id)
    
    if not invoice or invoice.studio_id != current_user.studio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    pdf_url = await service.generate_invoice_pdf(invoice_id)
    return {"pdf_url": pdf_url}