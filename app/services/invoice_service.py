"""Invoice service for billing and payment management."""

from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.schemas.invoices import (
    Invoice,
    InvoiceItem,
    InvoiceRequest,
    InvoiceUpdate,
    PaymentRequest,
    PaymentResponse,
    InvoiceStatus,
    RecurringInvoiceConfig
)


class InvoiceService:
    """Service for managing invoices and payments."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_invoice(
        self, 
        studio_id: str, 
        request: InvoiceRequest
    ) -> Invoice:
        """Create a new invoice."""
        # Calculate totals
        subtotal = sum(item.quantity * item.unit_price for item in request.items)
        tax_amount = subtotal * (request.tax_rate or 0)
        total_amount = subtotal + tax_amount
        
        # Generate invoice number
        invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{datetime.utcnow().microsecond}"
        
        # Mock invoice creation
        invoice = Invoice(
            id=f"inv_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            invoice_number=invoice_number,
            studio_id=studio_id,
            client_id=request.client_id,
            project_id=request.project_id,
            status=InvoiceStatus.DRAFT,
            issue_date=date.today(),
            due_date=request.due_date,
            items=request.items,
            subtotal=subtotal,
            tax_rate=request.tax_rate or 0,
            tax_amount=tax_amount,
            total_amount=total_amount,
            currency=request.currency or "USD",
            notes=request.notes,
            payment_terms=request.payment_terms,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        return invoice
    
    def get_invoice(self, invoice_id: str, studio_id: str) -> Optional[Invoice]:
        """Get invoice by ID."""
        # Mock implementation
        return Invoice(
            id=invoice_id,
            invoice_number="INV-20241014-001",
            studio_id=studio_id,
            client_id="client_001",
            project_id="proj_001",
            status=InvoiceStatus.SENT,
            issue_date=date.today() - timedelta(days=7),
            due_date=date.today() + timedelta(days=23),
            items=[
                InvoiceItem(
                    description="Wedding Photography Package",
                    quantity=1,
                    unit_price=Decimal("2500.00"),
                    total=Decimal("2500.00")
                ),
                InvoiceItem(
                    description="Additional Editing Hours",
                    quantity=5,
                    unit_price=Decimal("75.00"),
                    total=Decimal("375.00")
                )
            ],
            subtotal=Decimal("2875.00"),
            tax_rate=0.08,
            tax_amount=Decimal("230.00"),
            total_amount=Decimal("3105.00"),
            currency="USD",
            notes="Payment due within 30 days",
            payment_terms="Net 30",
            created_at=datetime.utcnow() - timedelta(days=7),
            updated_at=datetime.utcnow() - timedelta(days=7)
        )
    
    def list_invoices(
        self, 
        studio_id: str,
        status: Optional[InvoiceStatus] = None,
        client_id: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """List invoices with optional filtering."""
        # Mock invoice list
        invoices = [
            Invoice(
                id="inv_001",
                invoice_number="INV-20241014-001",
                studio_id=studio_id,
                client_id="client_001",
                status=InvoiceStatus.PAID,
                issue_date=date.today() - timedelta(days=30),
                due_date=date.today() - timedelta(days=7),
                subtotal=Decimal("2500.00"),
                tax_amount=Decimal("200.00"),
                total_amount=Decimal("2700.00"),
                currency="USD",
                created_at=datetime.utcnow() - timedelta(days=30)
            ),
            Invoice(
                id="inv_002",
                invoice_number="INV-20241014-002",
                studio_id=studio_id,
                client_id="client_002",
                status=InvoiceStatus.SENT,
                issue_date=date.today() - timedelta(days=14),
                due_date=date.today() + timedelta(days=16),
                subtotal=Decimal("1800.00"),
                tax_amount=Decimal("144.00"),
                total_amount=Decimal("1944.00"),
                currency="USD",
                created_at=datetime.utcnow() - timedelta(days=14)
            ),
            Invoice(
                id="inv_003",
                invoice_number="INV-20241014-003",
                studio_id=studio_id,
                client_id="client_003",
                status=InvoiceStatus.OVERDUE,
                issue_date=date.today() - timedelta(days=45),
                due_date=date.today() - timedelta(days=15),
                subtotal=Decimal("3200.00"),
                tax_amount=Decimal("256.00"),
                total_amount=Decimal("3456.00"),
                currency="USD",
                created_at=datetime.utcnow() - timedelta(days=45)
            )
        ]
        
        # Apply filters
        if status:
            invoices = [inv for inv in invoices if inv.status == status]
        if client_id:
            invoices = [inv for inv in invoices if inv.client_id == client_id]
        
        return {
            "invoices": invoices,
            "total": len(invoices),
            "page": page,
            "limit": limit,
            "pages": 1
        }
    
    def update_invoice(
        self, 
        invoice_id: str, 
        studio_id: str, 
        update: InvoiceUpdate
    ) -> Invoice:
        """Update an existing invoice."""
        # Mock update
        invoice = self.get_invoice(invoice_id, studio_id)
        if not invoice:
            raise ValueError("Invoice not found")
        
        # Update fields
        for field, value in update.dict(exclude_unset=True).items():
            setattr(invoice, field, value)
        
        invoice.updated_at = datetime.utcnow()
        return invoice
    
    def process_payment(
        self, 
        invoice_id: str, 
        payment_request: PaymentRequest
    ) -> PaymentResponse:
        """Process payment for an invoice."""
        # Mock payment processing
        payment_response = PaymentResponse(
            payment_id=f"pay_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            invoice_id=invoice_id,
            amount=payment_request.amount,
            currency=payment_request.currency,
            payment_method=payment_request.payment_method,
            status="completed",
            transaction_id=f"txn_{datetime.utcnow().microsecond}",
            processed_at=datetime.utcnow(),
            fees=payment_request.amount * Decimal("0.029"),  # 2.9% processing fee
            net_amount=payment_request.amount * Decimal("0.971")
        )
        
        return payment_response
    
    def send_invoice(self, invoice_id: str, studio_id: str) -> Dict[str, Any]:
        """Send invoice to client via email."""
        # Mock email sending
        return {
            "invoice_id": invoice_id,
            "status": "sent",
            "sent_at": datetime.utcnow().isoformat(),
            "recipient": "client@example.com",
            "subject": f"Invoice {invoice_id} from Your Studio",
            "delivery_status": "delivered"
        }
    
    def generate_pdf(self, invoice_id: str, studio_id: str) -> Dict[str, Any]:
        """Generate PDF version of invoice."""
        # Mock PDF generation
        return {
            "invoice_id": invoice_id,
            "pdf_url": f"/invoices/{invoice_id}/pdf",
            "generated_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
    
    def create_recurring_invoice(
        self, 
        studio_id: str, 
        config: RecurringInvoiceConfig
    ) -> Dict[str, Any]:
        """Set up recurring invoice."""
        # Mock recurring setup
        return {
            "recurring_id": f"rec_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "studio_id": studio_id,
            "client_id": config.client_id,
            "frequency": config.frequency,
            "next_invoice_date": config.start_date.isoformat(),
            "status": "active",
            "created_at": datetime.utcnow().isoformat()
        }
    
    def get_payment_analytics(self, studio_id: str) -> Dict[str, Any]:
        """Get payment and invoice analytics."""
        # Mock analytics
        return {
            "total_revenue": 45680.50,
            "outstanding_amount": 8944.00,
            "overdue_amount": 3456.00,
            "avg_payment_time": 18.5,  # days
            "payment_methods": {
                "credit_card": 67.3,
                "bank_transfer": 23.4,
                "paypal": 9.3
            },
            "monthly_revenue": [
                {"month": "2024-01", "revenue": 12500.00, "invoices": 8},
                {"month": "2024-02", "revenue": 15600.00, "invoices": 12},
                {"month": "2024-03", "revenue": 17580.50, "invoices": 15}
            ],
            "client_payment_behavior": {
                "on_time_payments": 78.2,
                "late_payments": 18.5,
                "partial_payments": 3.3
            }
        }