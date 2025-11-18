#!/usr/bin/env python3
"""
Seed Photo_Proof_v1 Mock Data to Database

This script migrates all mock data from Photo_Proof_v1/data/*.ts files
into the photo_proof_api database.

Usage:
    cd photo_proof_api
    source venv/bin/activate
    python seed_v1_mock_data.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.db import session_scope
from app.db.models import (
    Studio, User, Client, Project, Photo, 
    ServicePackage, Product, ProductOption,
    LayoutTemplate, Notification
)
from app.services.auth_service import AuthService


def create_demo_studio(session: Session) -> tuple[str, str]:
    """Create demo studio and return (studio_id, user_id)"""
    
    # Check if studio already exists
    existing_studio = session.query(Studio).filter_by(email="studio@photoproof.com").first()
    if existing_studio:
        print(f"✓ Studio already exists: {existing_studio.name}")
        user = session.query(User).filter_by(studio_id=existing_studio.id).first()
        return existing_studio.id, user.id if user else None
    
    studio_id = str(uuid4())
    user_id = str(uuid4())
    
    # Create studio
    studio = Studio(
        id=studio_id,
        name="NAPSTER's Photo Lab",
        email="studio@photoproof.com",
        phone="+1234567890",
        website="https://napsterphotolab.com",
        description="Professional photography services for weddings, portraits, and events",
        address="123 Photo Street, Studio City, CA 90001"
    )
    session.add(studio)
    
    # Create studio owner user
    user = User(
        id=user_id,
        email="studio@admin.com",  # Match the frontend login
        username="studio@admin.com",  # Match the frontend login
        password_hash=AuthService.hash_password("password123"),  # Match frontend password
        name="Studio Admin",
        role="studio_owner",
        studio_id=studio_id,
        is_active=True
    )
    session.add(user)
    
    session.commit()
    print(f"✓ Created studio: {studio.name}")
    print(f"✓ Created user: {user.email}")
    
    return studio_id, user_id


def seed_clients(session: Session, studio_id: str):
    """Seed demo clients from Photo_Proof_v1/data/clients.ts"""
    
    # Check if clients already exist
    existing_count = session.query(Client).filter_by(studio_id=studio_id).count()
    if existing_count > 0:
        print(f"✓ {existing_count} clients already exist")
        return
    
    clients_data = [
        {
            "name": "Emily & James",
            "email": "emily.james@email.com",
            "phone": "+1234567891",
            "username": "emily.james@email.com",
            "password": "wedding2024"
        },
        {
            "name": "Sarah Thompson",
            "email": "sarah.t@email.com",
            "phone": "+1234567892",
            "username": "sarah.t@email.com",
            "password": "portraits"
        },
        {
            "name": "Mike & Jessica",
            "email": "mike.jess@email.com",
            "phone": "+1234567893",
            "username": "mike.jess@email.com",
            "password": "engagement"
        }
    ]
    
    for client_data in clients_data:
        client_id = str(uuid4())
        user_id = str(uuid4())
        
        # Create client record
        client = Client(
            id=client_id,
            studio_id=studio_id,
            name=client_data["name"],
            email=client_data["email"],
            phone=client_data["phone"],
            status="active",
            user_id=user_id  # Link the user account
        )
        session.add(client)
        
        # Create user account for client
        user = User(
            id=user_id,
            email=client_data["username"],
            username=client_data["username"],
            password_hash=AuthService.hash_password(client_data["password"]),
            name=client_data["name"],
            role="client",
            studio_id=studio_id,
            is_active=True
        )
        session.add(user)
    
    session.commit()
    print(f"✓ Created {len(clients_data)} clients with login credentials")


def seed_service_packages(session: Session, studio_id: str):
    """Seed service packages from Photo_Proof_v1/data/services.ts"""
    
    # Check if packages already exist
    existing_count = session.query(ServicePackage).filter_by(studio_id=studio_id).count()
    if existing_count > 0:
        print(f"✓ {existing_count} service packages already exist")
        return
    
    packages_data = [
        {
            "name": "Essential",
            "category": "Wedding",
            "description": "Perfect for intimate weddings",
            "price": 150000,
            "features": [
                {"name": "4 hours coverage", "included": True},
                {"name": "1 photographer", "included": True},
                {"name": "200 edited photos", "included": True},
                {"name": "Online gallery", "included": True},
                {"name": "Print release", "included": True}
            ]
        },
        {
            "name": "Premium",
            "category": "Wedding",
            "description": "Our most popular package",
            "price": 250000,
            "features": [
                {"name": "8 hours coverage", "included": True},
                {"name": "2 photographers", "included": True},
                {"name": "400 edited photos", "included": True},
                {"name": "Engagement session", "included": True},
                {"name": "Online gallery", "included": True},
                {"name": "Print release", "included": True},
                {"name": "Photo album design", "included": True}
            ]
        },
        {
            "name": "Luxury",
            "category": "Wedding",
            "description": "Complete coverage for your special day",
            "price": 400000,
            "features": [
                {"name": "12 hours coverage", "included": True},
                {"name": "3 photographers", "included": True},
                {"name": "Unlimited photos", "included": True},
                {"name": "Engagement session", "included": True},
                {"name": "Online gallery", "included": True},
                {"name": "Print release", "included": True},
                {"name": "Custom photo album", "included": True},
                {"name": "Video highlights", "included": True}
            ]
        },
        {
            "name": "Studio Session",
            "category": "Portrait",
            "description": "Professional studio portraits",
            "price": 15000,
            "features": [
                {"name": "1 hour session", "included": True},
                {"name": "Studio location", "included": True},
                {"name": "20 edited photos", "included": True},
                {"name": "Online gallery", "included": True}
            ]
        },
        {
            "name": "Outdoor Session",
            "category": "Portrait",
            "description": "Natural light outdoor portraits",
            "price": 20000,
            "features": [
                {"name": "1.5 hour session", "included": True},
                {"name": "Outdoor location", "included": True},
                {"name": "30 edited photos", "included": True},
                {"name": "Online gallery", "included": True},
                {"name": "Print release", "included": True}
            ]
        }
    ]
    
    for pkg_data in packages_data:
        package = ServicePackage(
            id=str(uuid4()),
            studio_id=studio_id,
            name=pkg_data["name"],
            category=pkg_data["category"],
            description=pkg_data["description"],
            price=pkg_data["price"],
            features=pkg_data["features"]
        )
        session.add(package)
    
    session.commit()
    print(f"✓ Created {len(packages_data)} service packages")


def seed_products(session: Session):
    """Seed products from Photo_Proof_v1/data/products.ts"""
    
    # Check if products already exist
    existing_count = session.query(Product).count()
    if existing_count > 0:
        print(f"✓ {existing_count} products already exist")
        return
    
    products_data = [
        {
            "name": "Digital Download",
            "description": "High-resolution digital file",
            "product_type": "digital",
            "base_price": 5000,
            "options": []
        },
        {
            "name": "Standard Print",
            "description": "Professional quality photo print",
            "product_type": "print",
            "base_price": 2000,
            "options": [
                {"name": "4x6", "price_modifier": 0},
                {"name": "5x7", "price_modifier": 500},
                {"name": "8x10", "price_modifier": 1500},
                {"name": "11x14", "price_modifier": 3000}
            ]
        },
        {
            "name": "Canvas Print",
            "description": "Gallery-wrapped canvas",
            "product_type": "canvas",
            "base_price": 10000,
            "options": [
                {"name": "12x16", "price_modifier": 0},
                {"name": "16x20", "price_modifier": 5000},
                {"name": "20x30", "price_modifier": 10000},
                {"name": "24x36", "price_modifier": 15000}
            ]
        },
        {
            "name": "Photo Album",
            "description": "Custom designed photo album",
            "product_type": "album",
            "base_price": 35000,
            "options": [
                {"name": "20 pages", "price_modifier": 0},
                {"name": "30 pages", "price_modifier": 10000},
                {"name": "40 pages", "price_modifier": 20000}
            ]
        },
        {
            "name": "Framed Print",
            "description": "Professional framing included",
            "product_type": "frame",
            "base_price": 15000,
            "options": [
                {"name": "8x10 Black Frame", "price_modifier": 0},
                {"name": "8x10 White Frame", "price_modifier": 0},
                {"name": "11x14 Black Frame", "price_modifier": 5000},
                {"name": "11x14 White Frame", "price_modifier": 5000}
            ]
        }
    ]
    
    for prod_data in products_data:
        product_id = str(uuid4())
        product = Product(
            id=product_id,
            name=prod_data["name"],
            description=prod_data["description"],
            product_type=prod_data["product_type"],
            base_price=prod_data["base_price"],
            is_active=True
        )
        session.add(product)
        
        # Add product options
        for opt_data in prod_data["options"]:
            option = ProductOption(
                id=str(uuid4()),
                product_id=product_id,
                name=opt_data["name"],
                price_modifier=opt_data["price_modifier"],
                is_default=(opt_data == prod_data["options"][0]) if prod_data["options"] else False
            )
            session.add(option)
    
    session.commit()
    print(f"✓ Created {len(products_data)} products with options")


def seed_demo_projects(session: Session, studio_id: str):
    """Create demo projects (albums) with photos"""
    
    # Check if projects already exist
    existing_count = session.query(Project).filter_by(studio_id=studio_id).count()
    if existing_count > 0:
        print(f"✓ {existing_count} projects already exist")
        return
    
    # Get first client for demo projects
    client = session.query(Client).filter_by(studio_id=studio_id).first()
    if not client:
        print("⚠ No clients found, skipping project creation")
        return
    
    projects_data = [
        {
            "name": "Wedding - Emily & James",
            "description": "Beautiful summer wedding ceremony and reception",
            "client_name": "Emily & James",
            "client_email": "emily.james@email.com",
            "status": "delivered",
            "photo_count": 15
        },
        {
            "name": "Engagement - Mike & Jessica",
            "description": "Sunset engagement session at the beach",
            "client_name": "Mike & Jessica",
            "client_email": "mike.jess@email.com",
            "status": "active",
            "photo_count": 10
        },
        {
            "name": "Family Portraits - Thompson Family",
            "description": "Annual family portrait session",
            "client_name": "Sarah Thompson",
            "client_email": "sarah.t@email.com",
            "status": "active",
            "photo_count": 8
        }
    ]
    
    for proj_data in projects_data:
        project_id = str(uuid4())
        project = Project(
            id=project_id,
            studio_id=studio_id,
            client_id=client.id,
            name=proj_data["name"],
            description=proj_data["description"],
            client_name=proj_data["client_name"],
            client_email=proj_data["client_email"],
            status=proj_data["status"],
            watermark_enabled=True,
            comment_enabled=True,
            download_enabled=True,
            access_url=f"demo-{project_id[:8]}"
        )
        session.add(project)
        
        # Add demo photos to project
        for i in range(proj_data["photo_count"]):
            photo_id = str(uuid4())
            photo = Photo(
                id=photo_id,
                project_id=project_id,
                original_file_name=f"photo_{i+1:03d}.jpg",
                file_path=f"https://picsum.photos/800/600?random={photo_id[:8]}",
                thumbnail_path=f"https://picsum.photos/400/300?random={photo_id[:8]}",
                medium_path=f"https://picsum.photos/800/600?random={photo_id[:8]}",
                file_size=2500000 + (i * 100000),
                width=4000,
                height=3000,
                is_favorite=False,
                is_selected=False,
                order_index=i
            )
            session.add(photo)
    
    session.commit()
    print(f"✓ Created {len(projects_data)} demo projects with photos")


def main():
    """Main seeding function"""
    
    print("\n" + "="*60)
    print("Photo Proof - Seeding Mock Data from Photo_Proof_v1")
    print("="*60 + "\n")
    
    with session_scope() as session:
        # 1. Create demo studio
        print("1. Creating demo studio...")
        studio_id, user_id = create_demo_studio(session)
        
        # 2. Seed clients
        print("\n2. Seeding clients...")
        seed_clients(session, studio_id)
        
        # 3. Seed service packages
        print("\n3. Seeding service packages...")
        seed_service_packages(session, studio_id)
        
        # 4. Seed products
        print("\n4. Seeding products...")
        seed_products(session)
        
        # 5. Seed demo projects
        print("\n5. Seeding demo projects...")
        seed_demo_projects(session, studio_id)
    
    print("\n" + "="*60)
    print("✓ Data seeding complete!")
    print("="*60)
    print("\nDemo Credentials:")
    print("-" * 60)
    print("Studio Login:")
    print("  Email:    studio@admin.com")
    print("  Password: password123")
    print("\nClient Logins:")
    print("  Emily & James:    emily.james@email.com / wedding2024")
    print("  Sarah Thompson:   sarah.t@email.com / portraits")
    print("  Mike & Jessica:   mike.jess@email.com / engagement")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
