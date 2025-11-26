#!/usr/bin/env python3
"""Create test contracts for demo purposes."""

import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, '.')

from app.db.models import Contract, ContractTemplate, Studio, Client

# Database connection
engine = create_engine('sqlite:///photo_proof.db')
Session = sessionmaker(bind=engine)
db = Session()

try:
    # Get first studio
    studio = db.query(Studio).first()
    if not studio:
        print("❌ No studio found. Please create a studio first.")
        sys.exit(1)
    
    print(f"✅ Using studio: {studio.name} (ID: {studio.id})")
    
    # Get first client
    client = db.query(Client).filter(Client.studio_id == studio.id).first()
    if not client:
        print("❌ No client found. Please create a client first.")
        sys.exit(1)
    
    print(f"✅ Using client: {client.name} (ID: {client.id})")
    
    # Create a template if none exists
    template = db.query(ContractTemplate).filter(
        ContractTemplate.studio_id == studio.id,
        ContractTemplate.name == "Standard Photography Contract"
    ).first()
    
    if not template:
        print("Creating standard contract template...")
        template = ContractTemplate(
            studio_id=studio.id,
            name="Standard Photography Contract",
            category="wedding",
            content="""PHOTOGRAPHY SERVICES AGREEMENT

This agreement is entered into on {{contract_date}} between {{studio_name}} ("Photographer") and {{client_name}} ("Client").

1. SERVICES
The Photographer agrees to provide photography services for {{project_name}} on {{shoot_date}}.

2. DELIVERABLES
- {{photo_count}} edited high-resolution images
- Online gallery for {{gallery_days}} days
- Print rights for personal use

3. PAYMENT
Total Fee: ${{total_price}}
Deposit: ${{deposit_amount}} (due upon signing)
Balance: ${{balance_amount}} (due {{balance_due_date}})

4. COPYRIGHT
The Photographer retains copyright to all images. Client receives a license for personal use only.

5. CANCELLATION
Either party may cancel with {{cancellation_days}} days notice. Deposit is non-refundable.

By signing below, both parties agree to the terms of this contract.

Photographer: {{studio_name}}
Client: {{client_name}}
Date: {{contract_date}}""",
            variables={
                "contract_date": "date",
                "studio_name": "text",
                "client_name": "text",
                "project_name": "text",
                "shoot_date": "date",
                "photo_count": "number",
                "gallery_days": "number",
                "total_price": "currency",
                "deposit_amount": "currency",
                "balance_amount": "currency",
                "balance_due_date": "date",
                "cancellation_days": "number"
            },
            is_active=True
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        print(f"✅ Created template: {template.name}")
    else:
        print(f"✅ Using existing template: {template.name}")
    
    # Create test contracts
    contracts_to_create = [
        {
            "title": "Wedding Photography - Johnson Wedding",
            "status": "draft",
            "content": "This is a draft contract for the Johnson wedding photography services...",
        },
        {
            "title": "Portrait Session - Smith Family",
            "status": "sent",
            "content": "Portrait photography contract for the Smith family session...",
            "sent_at": datetime.utcnow() - timedelta(days=5),
        },
        {
            "title": "Corporate Headshots - Tech Corp",
            "status": "viewed",
            "content": "Corporate headshot photography services for Tech Corp employees...",
            "sent_at": datetime.utcnow() - timedelta(days=10),
            "viewed_at": datetime.utcnow() - timedelta(days=7),
        },
        {
            "title": "Event Coverage - Charity Gala",
            "status": "signed",
            "content": "Event photography contract for annual charity gala...",
            "sent_at": datetime.utcnow() - timedelta(days=20),
            "viewed_at": datetime.utcnow() - timedelta(days=18),
            "signed_at": datetime.utcnow() - timedelta(days=15),
        },
        {
            "title": "Product Photography - E-commerce Store",
            "status": "signed",
            "content": "Product photography services for e-commerce catalog...",
            "sent_at": datetime.utcnow() - timedelta(days=30),
            "viewed_at": datetime.utcnow() - timedelta(days=28),
            "signed_at": datetime.utcnow() - timedelta(days=25),
        },
    ]
    
    for i, contract_data in enumerate(contracts_to_create):
        # Check if similar contract exists
        existing = db.query(Contract).filter(
            Contract.studio_id == studio.id,
            Contract.title == contract_data["title"]
        ).first()
        
        if existing:
            print(f"⏭️  Contract already exists: {contract_data['title']}")
            continue
        
        contract_number = f"CONT-{datetime.now().year}-{1000 + i}"
        
        contract = Contract(
            studio_id=studio.id,
            client_id=client.id,
            template_id=template.id,
            contract_number=contract_number,
            title=contract_data["title"],
            content=contract_data["content"],
            status=contract_data["status"],
            sent_at=contract_data.get("sent_at"),
            viewed_at=contract_data.get("viewed_at"),
            signed_at=contract_data.get("signed_at"),
            expires_at=datetime.utcnow() + timedelta(days=30) if contract_data["status"] in ["sent", "viewed"] else None,
        )
        
        db.add(contract)
        print(f"✅ Created contract: {contract_data['title']} (Status: {contract_data['status']})")
    
    db.commit()
    print("\n✅ All test contracts created successfully!")
    
    # Print summary
    total = db.query(Contract).filter(Contract.studio_id == studio.id).count()
    draft = db.query(Contract).filter(Contract.studio_id == studio.id, Contract.status == "draft").count()
    sent = db.query(Contract).filter(Contract.studio_id == studio.id, Contract.status == "sent").count()
    viewed = db.query(Contract).filter(Contract.studio_id == studio.id, Contract.status == "viewed").count()
    signed = db.query(Contract).filter(Contract.studio_id == studio.id, Contract.status == "signed").count()
    
    print(f"\n📊 Contract Summary:")
    print(f"   Total: {total}")
    print(f"   Draft: {draft}")
    print(f"   Sent: {sent}")
    print(f"   Viewed: {viewed}")
    print(f"   Signed: {signed}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
