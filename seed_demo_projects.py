"""
Seed Demo Projects
Populate the database with sample projects/albums with photos
"""

import sys
sys.path.insert(0, '/Users/ns632@apac.comcast.com/Documents/v0_photo_proof/photo_proof_api')

from app.db.session import SessionLocal

# Import directly from the consolidated models.py file
from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declarative_base
import importlib.util
spec = importlib.util.spec_from_file_location("models", "/Users/ns632@apac.comcast.com/Documents/v0_photo_proof/photo_proof_api/app/db/models.py")
models_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models_module)

Project = models_module.Project
Category = models_module.Category
Image = models_module.Image
ProjectSettings = models_module.ProjectSettings
Studio = models_module.Studio
Client = models_module.Client
User = models_module.User
ServicePackage = models_module.ServicePackage

import uuid
from datetime import datetime, timedelta
import random

def seed_demo_projects():
    db = SessionLocal()
    
    try:
        # Check if projects already exist
        existing = db.query(Project).count()
        if existing > 0:
            print(f"Projects already exist ({existing} projects). Skipping...")
            return
        
        # Get first studio, clients, and a studio user
        studio = db.query(Studio).first()
        if not studio:
            print("No studio found! Please create a studio first.")
            return
        
        # Get a studio user to be the creator
        studio_user = db.query(User).filter(User.role == 'studio_owner').first()
        if not studio_user:
            print("No studio user found! Please run seed_demo_users.py first.")
            return
        
        clients = db.query(Client).all()
        if not clients:
            print("No clients found! Please run seed_demo_users.py first.")
            return
        
        print(f"Seeding projects for studio: {studio.name}")
        print(f"Found {len(clients)} clients")
        print(f"Using creator: {studio_user.email}")
        
        # Sample project data
        project_templates = [
            {
                "name": "Emily & James - Vineyard Wedding",
                "description": "Beautiful vineyard wedding ceremony and reception",
                "status": "active",
                "delivery_date": datetime.utcnow() + timedelta(days=14),
                "location": "Sonoma Valley Vineyard",
                "photo_count": 245
            },
            {
                "name": "Sarah's Maternity Session",
                "description": "Outdoor maternity photography in golden hour",
                "status": "delivered",
                "delivery_date": datetime.utcnow() - timedelta(days=7),
                "location": "Riverside Park",
                "photo_count": 32
            },
            {
                "name": "Mike & Jessica - Engagement Shoot",
                "description": "Urban engagement session in downtown",
                "status": "active",
                "delivery_date": datetime.utcnow() + timedelta(days=5),
                "location": "Downtown District",
                "photo_count": 58
            },
            {
                "name": "Thompson Family Portraits",
                "description": "Annual family portrait session",
                "status": "delivered",
                "delivery_date": datetime.utcnow() - timedelta(days=30),
                "location": "Studio",
                "photo_count": 45
            },
            {
                "name": "Emily & James - Pre-Wedding Shoot",
                "description": "Casual pre-wedding photo session at the beach",
                "status": "delivered",
                "delivery_date": datetime.utcnow() - timedelta(days=60),
                "location": "Pacific Beach",
                "photo_count": 67
            }
        ]
        
        created_projects = []
        
        for idx, template in enumerate(project_templates):
            # Assign to a client (cycle through available clients)
            client = clients[idx % len(clients)]
            
            # Create project
            project_id = str(uuid.uuid4())
            project = Project(
                id=project_id,
                studio_id=studio.id,
                client_id=client.id,
                name=template["name"],
                description=template["description"],
                status=template["status"],
                access_url=f"/gallery/{project_id}",
                delivery_date=template["delivery_date"],
                location=template["location"],
                view_count=random.randint(0, 50),
                total_images=0  # Will be updated when we add images
            )
            # Set created_by separately to avoid SQLAlchemy issue
            project.created_by = studio_user.id
            project.created_at = datetime.utcnow() - timedelta(days=random.randint(1, 90))
            project.updated_at = datetime.utcnow()
            db.add(project)
            db.flush()  # Get the project ID
            
            # Create default categories for this project
            categories = [
                {"name": "all", "display_name": "All Photos", "is_default": True, "order_index": 1},
                {"name": "favorites", "display_name": "Favorites", "is_default": False, "order_index": 2},
                {"name": "highlights", "display_name": "Highlights", "is_default": False, "order_index": 3}
            ]
            
            created_categories = {}
            for cat_data in categories:
                category = Category(
                    id=str(uuid.uuid4()),
                    project_id=project.id,
                    name=cat_data["name"],
                    display_name=cat_data["display_name"],
                    is_default=cat_data["is_default"],
                    order_index=cat_data["order_index"]
                )
                db.add(category)
                db.flush()
                created_categories[cat_data["name"]] = category
            
            # Create project settings
            settings = ProjectSettings(
                id=str(uuid.uuid4()),
                project_id=project.id,
                allow_comments=True,
                allow_favorites=True,
                allow_selections=True,
                allow_downloads=template["status"] == "delivered",
                watermark_enabled=True,
                is_password_protected=False
            )
            db.add(settings)
            
            # Create sample images for this project
            # For simplicity, we'll create image records without actual files
            # In a real scenario, you'd upload actual image files
            photo_count = template["photo_count"]
            for photo_idx in range(min(photo_count, 10)):  # Create up to 10 sample images per project
                image_id = str(uuid.uuid4())
                image = Image(
                    id=image_id,
                    project_id=project.id,
                    category_id=created_categories["all"].id,
                    uploaded_by=studio_user.id,
                    original_filename=f"photo_{photo_idx + 1:03d}.jpg",
                    s3_key_original=f"projects/{project.id}/originals/photo_{photo_idx + 1:03d}.jpg",
                    s3_key_thumbnail=f"projects/{project.id}/thumbnails/photo_{photo_idx + 1:03d}.jpg",
                    s3_key_preview=f"projects/{project.id}/previews/photo_{photo_idx + 1:03d}.jpg",
                    s3_key_print=f"projects/{project.id}/prints/photo_{photo_idx + 1:03d}.jpg",
                    file_size_bytes=random.randint(2000000, 8000000),  # 2-8 MB
                    mime_type="image/jpeg",
                    width=random.choice([3840, 4096, 5120, 6000]),
                    height=random.choice([2160, 2730, 3413, 4000]),
                    captured_at=datetime.utcnow() - timedelta(days=random.randint(1, 90)),
                    camera_make=random.choice(["Canon", "Nikon", "Sony", "Fujifilm"]),
                    camera_model=random.choice(["EOS R5", "Z9", "A7IV", "X-T4"]),
                    rating=random.choice([0, 0, 0, 3, 4, 5]),  # Most unrated, some rated
                    is_favorite=random.choice([True, False, False, False]),  # ~25% favorites
                    is_selected=random.choice([True, False, False, False]),  # ~25% selected
                    comment_count=random.randint(0, 5),
                    status="active"
                )
                db.add(image)
            
            # Update project total_images
            project.total_images = min(photo_count, 10)
            
            created_projects.append(project)
            print(f"  ✓ Created project: {project.name} ({project.total_images} photos)")
        
        db.commit()
        print(f"\n✅ Successfully seeded {len(created_projects)} projects!")
        print(f"   Total images created: {sum(p.total_images for p in created_projects)}")
        
    except Exception as e:
        print(f"❌ Error seeding projects: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_projects()
