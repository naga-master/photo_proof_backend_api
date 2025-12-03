"""Contract management service."""

import hashlib
import io
import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
import base64

from jinja2 import Template
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from PIL import Image as PILImage
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models import (
    Contract,
    ContractTemplate,
    ContractActivity,
    ContractEmailTemplate,
    Studio,
    Client,
    Project,
    User
)


class ContractService:
    """Service for contract management operations."""
    
    def __init__(self, db: Session):
        """Initialize contract service."""
        self.db = db
        
    def generate_contract_number(self, studio_id: str) -> str:
        """Generate unique contract number."""
        # Get studio prefix (first 3 letters of studio name)
        studio = self.db.query(Studio).filter(Studio.id == studio_id).first()
        prefix = studio.name[:3].upper() if studio else "CNT"
        
        # Generate timestamp-based number
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M")
        
        # Add random suffix for uniqueness
        suffix = secrets.token_hex(2).upper()
        
        return f"{prefix}-{timestamp}-{suffix}"
    
    def render_template(self, template_content: str, variables: Dict[str, Any]) -> str:
        """Render contract template with variables."""
        template = Template(template_content)
        return template.render(**variables)
    
    async def create_contract(
        self,
        studio_id: str,
        client_id: int,  # Client.id is Integer, not String
        template_id: Optional[str],
        title: str,
        content: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None,
        expires_days: int = 30
    ) -> Contract:
        """Create new contract from template or custom content."""
        
        # If template_id provided, get template and render
        if template_id:
            template = self.db.query(ContractTemplate).filter(
                and_(
                    ContractTemplate.id == template_id,
                    ContractTemplate.studio_id == studio_id,
                    ContractTemplate.is_active == True
                )
            ).first()
            
            if not template:
                raise ValueError("Template not found or inactive")
            
            # Render template with variables
            if variables:
                content = self.render_template(template.content, variables)
            else:
                content = template.content
        
        if not content:
            raise ValueError("Contract content is required")
        
        # Generate unique contract number
        contract_number = self.generate_contract_number(studio_id)
        
        # Create contract
        contract = Contract(
            studio_id=studio_id,
            client_id=client_id,
            project_id=project_id,
            template_id=template_id,
            contract_number=contract_number,
            title=title,
            content=content,
            status="draft",
            expires_at=datetime.utcnow() + timedelta(days=expires_days),
            terms=variables
        )
        
        # Generate PDF
        pdf_path = await self.generate_pdf(contract)
        contract.pdf_url = pdf_path
        
        # Add to database
        self.db.add(contract)
        self.db.commit()
        self.db.refresh(contract)
        
        # Log activity (after commit so contract.id is available)
        self.log_activity(contract.id, "created", None, {"source": "api"})
        self.db.commit()  # Commit the activity log
        
        return contract
    
    async def generate_pdf(self, contract: Contract) -> str:
        """Generate PDF from contract."""
        # Create uploads directory if not exists
        upload_dir = Path("uploads") / "contracts" / contract.studio_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # PDF file path
        pdf_filename = f"{contract.contract_number}.pdf"
        pdf_path = upload_dir / pdf_filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor='black',
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor='black',
            spaceAfter=12,
            spaceBefore=12
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            textColor='black',
            alignment=TA_JUSTIFY,
            spaceAfter=12
        )
        
        # Add title
        elements.append(Paragraph(contract.title, title_style))
        elements.append(Spacer(1, 12))
        
        # Add contract number and date
        # Use created_at if available, otherwise use current time (for contracts not yet committed)
        contract_date = contract.created_at if contract.created_at else datetime.utcnow()
        info_text = f"Contract Number: {contract.contract_number}<br/>Date: {contract_date.strftime('%B %d, %Y')}"
        elements.append(Paragraph(info_text, body_style))
        elements.append(Spacer(1, 24))
        
        # Add contract content
        # Split content into paragraphs
        content_lines = contract.content.split('\n')
        for line in content_lines:
            if line.strip():
                # Check if it's a heading (starts with #)
                if line.strip().startswith('#'):
                    heading_text = line.strip('#').strip()
                    elements.append(Paragraph(heading_text, heading_style))
                else:
                    elements.append(Paragraph(line, body_style))
            else:
                elements.append(Spacer(1, 6))
        
        # Add signature section
        elements.append(Spacer(1, 48))
        elements.append(Paragraph("SIGNATURES", heading_style))
        elements.append(Spacer(1, 24))
        
        # Client signature line
        sig_table_data = [
            ["_" * 50, "_" * 20],
            ["Client Signature", "Date"],
            ["", ""],
            ["_" * 50, "_" * 20],
            ["Studio Representative", "Date"]
        ]
        
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib import colors
        
        sig_table = Table(sig_table_data, colWidths=[3.5*inch, 2*inch])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, 1), 10),
            ('FONTNAME', (0, 4), (-1, 4), 'Helvetica'),
            ('FONTSIZE', (0, 4), (-1, 4), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 20),
            ('BOTTOMPADDING', (0, 3), (-1, 3), 20),
        ]))
        
        elements.append(sig_table)
        
        # Build PDF
        doc.build(elements)
        
        # Return relative path for storage
        return f"/contracts/{contract.studio_id}/{pdf_filename}"
    
    async def generate_signed_pdf(self, contract: Contract) -> str:
        """Generate signed PDF with signature image."""
        if not contract.client_signature:
            raise ValueError("Contract has no signature")
        
        # Create uploads directory
        upload_dir = Path("uploads") / "contracts" / contract.studio_id / "signed"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # PDF file path
        pdf_filename = f"{contract.contract_number}_signed.pdf"
        pdf_path = upload_dir / pdf_filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        elements = []
        
        # Define styles (same as before)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor='black',
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            textColor='black',
            alignment=TA_JUSTIFY,
            spaceAfter=12
        )
        
        # Add title and content
        elements.append(Paragraph(contract.title, title_style))
        elements.append(Spacer(1, 12))
        
        # Use created_at if available, otherwise use current time
        contract_date = contract.created_at if contract.created_at else datetime.utcnow()
        info_text = f"Contract Number: {contract.contract_number}<br/>Date: {contract_date.strftime('%B %d, %Y')}"
        elements.append(Paragraph(info_text, body_style))
        elements.append(Spacer(1, 24))
        
        # Add contract content
        content_lines = contract.content.split('\n')
        for line in content_lines:
            if line.strip():
                elements.append(Paragraph(line, body_style))
            else:
                elements.append(Spacer(1, 6))
        
        # Add signature section with actual signature
        elements.append(Spacer(1, 48))
        elements.append(Paragraph("SIGNATURES", styles['Heading2']))
        elements.append(Spacer(1, 24))
        
        # Process signature image
        if contract.client_signature.startswith('data:image'):
            # Extract base64 data
            header, data = contract.client_signature.split(',', 1)
            image_data = base64.b64decode(data)
            
            # Save signature image temporarily
            sig_image_path = upload_dir / f"{contract.contract_number}_signature.png"
            with open(sig_image_path, 'wb') as f:
                f.write(image_data)
            
            # Add signature image to PDF
            sig_img = RLImage(str(sig_image_path), width=2*inch, height=0.75*inch)
            elements.append(sig_img)
        
        # Add signature details
        sig_info = f"""
        Signed by: {contract.client.name if contract.client else 'Unknown'}<br/>
        Date: {contract.signed_at.strftime('%B %d, %Y %H:%M UTC') if contract.signed_at else 'N/A'}<br/>
        IP Address: {contract.client_ip or 'N/A'}<br/>
        Signature Hash: {contract.client_signature_hash[:16]}...
        """
        elements.append(Paragraph(sig_info, body_style))
        
        # Build PDF
        doc.build(elements)
        
        # Return relative path
        return f"/contracts/{contract.studio_id}/signed/{pdf_filename}"
    
    async def send_contract(self, contract_id: str, recipient_email: str) -> bool:
        """Send contract for signature."""
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError("Contract not found")
        
        # Update contract status
        contract.status = "sent"
        contract.sent_at = datetime.utcnow()
        
        # Log activity
        self.log_activity(contract_id, "sent", None, {"recipient": recipient_email})
        
        self.db.commit()
        
        # TODO: Implement actual email sending
        # For now, just return True
        return True
    
    async def sign_contract(
        self,
        contract_id: str,
        signature_data: str,
        client_info: Dict[str, str]
    ) -> Contract:
        """Process contract signature."""
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError("Contract not found")
        
        # Check if contract can be signed
        if contract.status not in ["sent", "viewed"]:
            raise ValueError("Contract cannot be signed in current status")
        
        # Check if contract expired
        if contract.expires_at and contract.expires_at < datetime.utcnow():
            raise ValueError("Contract has expired")
        
        # Generate signature hash
        signature_hash = hashlib.sha256(signature_data.encode()).hexdigest()
        
        # Update contract
        contract.client_signature = signature_data
        contract.client_signature_hash = signature_hash
        contract.client_ip = client_info.get('ip')
        contract.client_user_agent = client_info.get('user_agent')
        contract.signed_at = datetime.utcnow()
        contract.status = "signed"
        
        # Generate signed PDF
        signed_pdf = await self.generate_signed_pdf(contract)
        contract.signed_pdf_url = signed_pdf
        
        # Log activity
        self.log_activity(
            contract_id,
            "signed",
            None,
            {
                "ip": client_info.get('ip'),
                "user_agent": client_info.get('user_agent')
            }
        )
        
        self.db.commit()
        self.db.refresh(contract)
        
        # TODO: Send confirmation emails
        
        return contract
    
    async def verify_signature(self, contract_id: str) -> bool:
        """Verify contract signature authenticity."""
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            return False
        
        if not contract.client_signature or not contract.client_signature_hash:
            return False
        
        # Recalculate hash
        calculated_hash = hashlib.sha256(contract.client_signature.encode()).hexdigest()
        
        # Compare with stored hash
        return calculated_hash == contract.client_signature_hash
    
    def log_activity(
        self,
        contract_id: str,
        action: str,
        actor_id: Optional[str],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log contract activity."""
        activity = ContractActivity(
            contract_id=contract_id,
            action=action,
            actor_id=actor_id,
            ip_address=metadata.get('ip') if metadata else None,
            user_agent=metadata.get('user_agent') if metadata else None,
            activity_metadata=metadata
        )
        self.db.add(activity)
    
    def get_contract(self, contract_id: str) -> Optional[Contract]:
        """Get contract by ID."""
        return self.db.query(Contract).filter(Contract.id == contract_id).first()
    
    def get_contracts_by_studio(
        self,
        studio_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Contract]:
        """Get contracts for a studio."""
        query = self.db.query(Contract).filter(Contract.studio_id == studio_id)
        
        if status:
            query = query.filter(Contract.status == status)
        
        return query.order_by(Contract.created_at.desc()).offset(offset).limit(limit).all()
    
    def get_contract_stats(self, studio_id: str) -> Dict[str, int]:
        """Get contract statistics for studio."""
        total = self.db.query(Contract).filter(Contract.studio_id == studio_id).count()
        draft = self.db.query(Contract).filter(
            and_(Contract.studio_id == studio_id, Contract.status == "draft")
        ).count()
        sent = self.db.query(Contract).filter(
            and_(Contract.studio_id == studio_id, Contract.status == "sent")
        ).count()
        signed = self.db.query(Contract).filter(
            and_(Contract.studio_id == studio_id, Contract.status == "signed")
        ).count()
        
        # Count expiring soon (within 7 days)
        expiring_date = datetime.utcnow() + timedelta(days=7)
        expiring = self.db.query(Contract).filter(
            and_(
                Contract.studio_id == studio_id,
                Contract.status.in_(["sent", "viewed"]),
                Contract.expires_at <= expiring_date
            )
        ).count()
        
        return {
            "total": total,
            "draft": draft,
            "pending": sent,
            "signed": signed,
            "expiring": expiring
        }
