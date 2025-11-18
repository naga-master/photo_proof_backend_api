"""
Seed Service Packages
Populate the database with sample service packages
"""

from app.db.session import SessionLocal
from app.db import models
import uuid
from datetime import datetime

def seed_service_packages():
    db = SessionLocal()
    
    try:
        # Check if packages already exist
        existing = db.query(models.ServicePackage).count()
        if existing > 0:
            print(f"Service packages already exist ({existing} packages). Skipping...")
            return
        
        # Get first studio (demo studio)
        studio = db.query(models.Studio).first()
        if not studio:
            print("No studio found! Please create a studio first.")
            return
        
        print(f"Seeding service packages for studio: {studio.name}")
        
        packages = [
            {
                "name": "Wedding Essential",
                "category": "Wedding",
                "description": "Perfect for intimate weddings",
                "price": 2500.00,
                "features": [
                    {"name": "6 Hours Coverage", "included": True},
                    {"name": "2 Photographers", "included": True},
                    {"name": "400+ Edited Photos", "included": True},
                    {"name": "Online Gallery", "included": True},
                    {"name": "Print Rights", "included": True},
                    {"name": "Engagement Session", "included": False},
                    {"name": "Wedding Album", "included": False},
                    {"name": "Second Shooter", "included": False}
                ]
            },
            {
                "name": "Wedding Premium",
                "category": "Wedding",
                "description": "Complete wedding coverage with all the extras",
                "price": 4500.00,
                "features": [
                    {"name": "10 Hours Coverage", "included": True},
                    {"name": "2 Photographers", "included": True},
                    {"name": "800+ Edited Photos", "included": True},
                    {"name": "Online Gallery", "included": True},
                    {"name": "Print Rights", "included": True},
                    {"name": "Engagement Session", "included": True},
                    {"name": "Wedding Album", "included": True},
                    {"name": "Second Shooter", "included": True}
                ]
            },
            {
                "name": "Portrait Session",
                "category": "Portrait",
                "description": "Professional portrait photography",
                "price": 350.00,
                "features": [
                    {"name": "1 Hour Session", "included": True},
                    {"name": "1 Location", "included": True},
                    {"name": "30+ Edited Photos", "included": True},
                    {"name": "Online Gallery", "included": True},
                    {"name": "Print Rights", "included": True},
                    {"name": "Multiple Locations", "included": False},
                    {"name": "Outfit Changes", "included": False},
                    {"name": "Props & Styling", "included": False}
                ]
            },
            {
                "name": "Family Package",
                "category": "Family",
                "description": "Capture your family memories",
                "price": 450.00,
                "features": [
                    {"name": "90 Minute Session", "included": True},
                    {"name": "2 Locations", "included": True},
                    {"name": "50+ Edited Photos", "included": True},
                    {"name": "Online Gallery", "included": True},
                    {"name": "Print Rights", "included": True},
                    {"name": "Outfit Changes", "included": True},
                    {"name": "Props Available", "included": True},
                    {"name": "Print Package", "included": False}
                ]
            },
            {
                "name": "Corporate Event",
                "category": "Event",
                "description": "Professional event photography",
                "price": 800.00,
                "features": [
                    {"name": "4 Hours Coverage", "included": True},
                    {"name": "1 Photographer", "included": True},
                    {"name": "200+ Edited Photos", "included": True},
                    {"name": "Online Gallery", "included": True},
                    {"name": "Print Rights", "included": True},
                    {"name": "Same Day Preview", "included": True},
                    {"name": "Additional Hours", "included": False},
                    {"name": "Videography", "included": False}
                ]
            },
            {
                "name": "Newborn Session",
                "category": "Newborn",
                "description": "Gentle newborn photography",
                "price": 550.00,
                "features": [
                    {"name": "3 Hour Session", "included": True},
                    {"name": "Studio Location", "included": True},
                    {"name": "40+ Edited Photos", "included": True},
                    {"name": "Online Gallery", "included": True},
                    {"name": "Print Rights", "included": True},
                    {"name": "Props & Wraps", "included": True},
                    {"name": "Family Photos", "included": True},
                    {"name": "Canvas Prints", "included": False}
                ]
            }
        ]
        
        for pkg_data in packages:
            package = models.ServicePackage(
                id=str(uuid.uuid4()),
                studio_id=studio.id,
                name=pkg_data["name"],
                category=pkg_data["category"],
                description=pkg_data["description"],
                price=pkg_data["price"],
                features=pkg_data["features"],
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(package)
            print(f"  ✓ Created package: {package.name} (${package.price})")
        
        db.commit()
        print(f"\n✅ Successfully seeded {len(packages)} service packages!")
        
    except Exception as e:
        print(f"❌ Error seeding service packages: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_service_packages()
