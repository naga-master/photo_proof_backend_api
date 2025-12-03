#!/usr/bin/env python3
"""
Create demo clients for testing
Seeds the database with sample clients for studio@admin.com
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import SessionLocal
from app.db.models.user import User, Client
from app.services.auth_service import AuthService

def create_demo_clients():
    """Create demo clients for the demo studio."""
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("Creating Demo Clients for Photo Proof")
        print("=" * 70)
        print()
        
        # Find demo studio user
        demo_user = db.query(User).filter(User.email == 'studio@admin.com').first()
        
        if not demo_user:
            print("❌ Demo user (studio@admin.com) not found!")
            print("Please ensure the user exists first.")
            return
        
        if not demo_user.studio_id:
            print("❌ Demo user has no studio_id!")
            return
        
        studio_id = demo_user.studio_id
        print(f"✅ Found demo studio: {studio_id}")
        print(f"   User: {demo_user.email} (ID: {demo_user.id})")
        print()
        
        # Demo clients data
        clients_data = [
            {
                "name": "John Smith",
                "email": "john.smith@example.com",
                "phone": "+1-555-0101",
                "address": "123 Main Street, New York, NY 10001",
                "username": "john.smith",
                "password": "demo123",
            },
            {
                "name": "Sarah Johnson",
                "email": "sarah.j@example.com",
                "phone": "+1-555-0102",
                "address": "456 Oak Avenue, Los Angeles, CA 90001",
                "username": "sarah.johnson",
                "password": "demo123",
            },
            {
                "name": "Mike Williams",
                "email": "mike.w@example.com",
                "phone": "+1-555-0103",
                "address": "789 Pine Road, Chicago, IL 60601",
                "username": "mike.williams",
                "password": "demo123",
            },
            {
                "name": "Emma Davis",
                "email": "emma.davis@example.com",
                "phone": "+1-555-0104",
                "address": "321 Elm Street, Houston, TX 77001",
                "username": "emma.davis",
                "password": "demo123",
            },
            {
                "name": "James Brown",
                "email": "james.brown@example.com",
                "phone": "+1-555-0105",
                "address": "654 Maple Drive, Phoenix, AZ 85001",
                "username": "james.brown",
                "password": "demo123",
            },
        ]
        
        created_count = 0
        skipped_count = 0
        
        print("Creating clients...")
        print("-" * 70)
        
        for data in clients_data:
            # Check if client already exists
            existing = db.query(Client).filter(
                Client.studio_id == studio_id,
                Client.email == data["email"]
            ).first()
            
            if existing:
                print(f"⏭️  {data['name']} ({data['email']}) - already exists")
                skipped_count += 1
                continue
            
            # Create client
            client = Client(
                studio_id=studio_id,
                name=data["name"],
                email=data["email"],
                phone=data["phone"],
                address=data.get("address"),
                username=data.get("username", data["email"]),
                password=AuthService.hash_password(data.get("password", "demo123")),
                status="active",
                whatsapp_opt_in=True,
                email_opt_in=True,
            )
            
            db.add(client)
            created_count += 1
            print(f"✅ Created: {data['name']} ({data['email']})")
            print(f"   Username: {data.get('username', data['email'])}")
            print(f"   Password: {data.get('password', 'demo123')}")
            print()
        
        db.commit()
        
        print("=" * 70)
        print(f"✅ Success!")
        print(f"   Created: {created_count} clients")
        print(f"   Skipped: {skipped_count} clients (already exist)")
        print("=" * 70)
        print()
        
        # Show all clients for this studio
        all_clients = db.query(Client).filter(Client.studio_id == studio_id).all()
        print(f"📊 Total clients in studio: {len(all_clients)}")
        print()
        print("All Clients:")
        print("-" * 70)
        for client in all_clients:
            print(f"  • {client.name} ({client.email})")
        print()
        
        print("🎉 Demo data ready!")
        print()
        print("You can now:")
        print("  1. Login as studio@admin.com")
        print("  2. Navigate to Clients page")
        print("  3. See the demo clients")
        print("  4. Create contracts and assign them to these clients")
        print()
        
    except Exception as e:
        db.rollback()
        print()
        print("=" * 70)
        print("❌ Error creating demo clients")
        print("=" * 70)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        db.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(create_demo_clients())
