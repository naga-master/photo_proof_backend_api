"""Seed database with initial data."""

from app.db.session import SessionLocal
from app.db.models import Studio, LayoutTemplate, User


def seed_database():
    """Populate database with demo data."""
    db = SessionLocal()
    
    try:
        print("🌱 Seeding database...")
        
        existing_studio = db.query(Studio).filter(Studio.email == "studio@photoproof.com").first()
        if not existing_studio:
            studio = Studio(
                id="studio_demo",
                name="Demo Photography Studio",
                email="studio@photoproof.com",
                phone="555-0123",
                address="123 Main Street, Suite 100",
                brand_color="#3b82f6",
                typography="Inter & Playfair Display",
                studio_description="Professional photography services for all occasions",
                subscription_tier="professional",
                subscription_status="active",
                max_projects=50,
                max_storage_gb=100,
            )
            db.add(studio)
            db.flush()
            
            owner = User(
                id="user_owner_demo",
                studio_id=studio.id,
                name="Studio Owner",
                email="studio@photoproof.com",
                username="studioowner",
                password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5OfmcQ6RQ.5Ba",
                role="studio_owner",
            )
            db.add(owner)
            print("  ✅ Created demo studio and owner user")
        else:
            print("  ℹ️  Demo studio already exists")
        
        layouts = [
            {"id": "layout1", "name": "Classic Cover Grid", "description": "Traditional layout with cover photo and masonry grid", "header": "Cover", "grid": "Masonry", "aspect": "Landscape", "theme": "White"},
            {"id": "layout2", "name": "Modern Grid - Portrait", "description": "Clean grid layout optimized for portrait photos", "header": "Title Only", "grid": "Grid", "aspect": "Portrait", "theme": "Gray"},
            {"id": "layout3", "name": "Stacked Elegance", "description": "Vertical stacked layout with cream theme", "header": "Cover", "grid": "Stacked", "aspect": "Landscape", "theme": "Cream"},
            {"id": "layout4", "name": "Dark Masonry", "description": "Modern masonry layout with dark theme", "header": "Title Only", "grid": "Masonry", "aspect": "Portrait", "theme": "Black"},
            {"id": "layout5", "name": "Portrait Grid White", "description": "Classic white grid for portrait orientation", "header": "Cover", "grid": "Grid", "aspect": "Portrait", "theme": "White"},
        ]
        
        layout_count = 0
        for layout_data in layouts:
            existing = db.query(LayoutTemplate).filter(LayoutTemplate.id == layout_data["id"]).first()
            if not existing:
                layout = LayoutTemplate(
                    id=layout_data["id"],
                    name=layout_data["name"],
                    description=layout_data["description"],
                    header=layout_data["header"],
                    grid=layout_data["grid"],
                    aspect=layout_data["aspect"],
                    theme=layout_data["theme"],
                )
                db.add(layout)
                layout_count += 1
        
        if layout_count > 0:
            print(f"  ✅ Created {layout_count} layout templates")
        else:
            print("  ℹ️  Layout templates already exist")
        
        db.commit()
        print("\n✨ Database seeding complete!")
        print("\n📝 Demo Credentials:")
        print("   Email: studio@photoproof.com")
        print("   Username: studioowner")
        print("   Password: password123")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
