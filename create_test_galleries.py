#!/usr/bin/env python3
"""Create test galleries for Photo Proof."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import session_scope
from app.db.models import Project, Studio, User, Client
from datetime import datetime, timedelta, timezone

def create_test_galleries():
    """Create test galleries for testing."""
    
    with session_scope() as session:
        # Get the demo studio
        studio = session.query(Studio).filter(Studio.subdomain == 'demo').first()
        if not studio:
            print("❌ Demo studio not found! Creating it...")
            studio = Studio(
                id='studio_demo',
                name='Demo Studio',
                subdomain='demo',
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(studio)
            session.commit()
        
        # Get studio owner
        studio_user = session.query(User).filter(
            User.email == 'studio@admin.com'
        ).first()
        
        if not studio_user:
            print("❌ Studio user not found!")
            return
        
        print(f"✅ Found studio: {studio.name}")
        print(f"✅ Found user: {studio_user.email}")
        print()
        
        # Create 5 test galleries
        galleries_data = [
            {
                'name': 'Summer Wedding - Sarah & Mike',
                'description': 'Beautiful outdoor wedding ceremony and reception',
                'status': 'active',
                'is_public': True,
            },
            {
                'name': 'Corporate Headshots - Tech Startup',
                'description': 'Professional headshots for company website',
                'status': 'active',
                'is_public': False,
            },
            {
                'name': 'Family Portrait Session - Johnson Family',
                'description': 'Annual family portraits at the park',
                'status': 'active',
                'is_public': True,
            },
            {
                'name': 'Product Photography - Fashion Brand',
                'description': 'New collection product shots',
                'status': 'draft',
                'is_public': False,
            },
            {
                'name': 'Engagement Photos - Emma & James',
                'description': 'Romantic engagement photo session at sunset',
                'status': 'active',
                'is_public': True,
            },
        ]
        
        created_count = 0
        for i, gallery_data in enumerate(galleries_data, 1):
            # Check if gallery already exists
            existing = session.query(Project).filter(
                Project.title == gallery_data['name'],
                Project.studio_id == studio.id
            ).first()
            
            if existing:
                print(f"⏭️  Skipping '{gallery_data['name']}' - already exists")
                continue
            
            # Create gallery
            gallery = Project(
                studio_id=studio.id,
                created_by_id=studio_user.id,
                title=gallery_data['name'],
                description=gallery_data['description'],
                status=gallery_data['status'],
                is_public=gallery_data['is_public'],
                created_at=datetime.utcnow() - timedelta(days=30-i*5),
                updated_at=datetime.utcnow() - timedelta(days=30-i*5),
            )
            session.add(gallery)
            created_count += 1
            print(f"✅ Created gallery: {gallery_data['name']}")
        
        session.commit()
        
        print()
        print("="*60)
        print(f"✅ Created {created_count} test galleries!")
        
        # Show all galleries
        all_galleries = session.query(Project).filter(
            Project.studio_id == studio.id
        ).all()
        
        print(f"📊 Total galleries in database: {len(all_galleries)}")
        print("="*60)
        print()
        print("Galleries:")
        for g in all_galleries:
            print(f"  ID: {g.id:3} | {g.title:40} | Status: {g.status:10} | Public: {g.is_public}")
        print()

if __name__ == '__main__':
    print("🚀 Creating test galleries...")
    print()
    create_test_galleries()
