#!/usr/bin/env python3
"""Create test data for Photo Proof mobile app."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import session_scope
from app.db.models import Project, Client, Studio, User
from datetime import datetime, timedelta

def create_test_projects():
    """Create test projects/galleries."""
    
    with session_scope() as session:
        # Get studio and client
        studio = session.query(Studio).filter(Studio.subdomain == 'demo').first()
        client = session.query(Client).filter(Client.id == 1).first()
        
        if not studio or not client:
            print("❌ Studio or Client not found!")
            return
        
        print(f"✅ Studio: {studio.name}")
        print(f"✅ Client: {client.name}")
        print()
        
        # Test projects data
        projects_data = [
            {
                'title': 'Summer Wedding - Sarah & Mike',
                'status': 'active',
                'photo_count': 150,
            },
            {
                'title': 'Corporate Headshots - Tech Startup',
                'status': 'active',
                'photo_count': 25,
            },
            {
                'title': 'Family Portrait Session',
                'status': 'active',
                'photo_count': 45,
            },
            {
                'title': 'Product Photography - Fashion Brand',
                'status': 'draft',
                'photo_count': 80,
            },
            {
                'title': 'Engagement Photos - Emma & James',
                'status': 'active',
                'photo_count': 60,
            },
        ]
        
        created_count = 0
        for i, data in enumerate(projects_data, 1):
            # Check if exists
            existing = session.query(Project).filter(
                Project.title == data['title'],
                Project.client_id == client.id
            ).first()
            
            if existing:
                print(f"⏭️  '{data['title']}' already exists")
                continue
            
            # Create project
            project = Project(
                studio_id=studio.id,
                client_id=client.id,
                title=data['title'],
                status=data['status'],
                photo_count=data['photo_count'],
                is_locked=False,
                layout='layout1',
                has_folders=False,
                created_at=datetime.utcnow() - timedelta(days=30-i*5),
                updated_at=datetime.utcnow() - timedelta(days=i),
            )
            session.add(project)
            created_count += 1
            print(f"✅ Created: {data['title']}")
        
        session.commit()
        
        print()
        print("="*70)
        print(f"✅ Created {created_count} new projects!")
        
        # Show all projects
        all_projects = session.query(Project).filter(
            Project.client_id == client.id
        ).all()
        
        print(f"📊 Total projects: {len(all_projects)}")
        print("="*70)
        print()
        print("Projects:")
        for p in all_projects:
            print(f"  ID: {p.id:3} | {p.title:45} | Photos: {p.photo_count:3} | Status: {p.status}")
        print()

if __name__ == '__main__':
    print("🚀 Creating test projects...")
    print()
    create_test_projects()
