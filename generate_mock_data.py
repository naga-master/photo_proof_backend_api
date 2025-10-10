"""
Mock Data Generator

Generates realistic mock data for testing the photo proofing system.
Creates 100-250+ images across multiple projects and categories.
"""

import uuid
from datetime import datetime, timedelta
from typing import List
import random

from models import (
    User, Studio, Project, ProjectImage, ProjectCategory, Comment,
    ProjectStatus, UserRole, ImageVersion, ImageMetadata, ProjectSettings
)
from data_manager import data_manager


# Picsum photos for realistic image URLs
PICSUM_BASE_URL = "https://picsum.photos"


def generate_image_url(width: int = 800, height: int = 600, seed: int = None) -> str:
    """Generate a Picsum photo URL"""
    if seed:
        return f"{PICSUM_BASE_URL}/seed/{seed}/{width}/{height}"
    return f"{PICSUM_BASE_URL}/{width}/{height}"


def generate_thumbnail_url(width: int = 300, height: int = 200, seed: int = None) -> str:
    """Generate a thumbnail URL"""
    if seed:
        return f"{PICSUM_BASE_URL}/seed/{seed}/{width}/{height}"
    return f"{PICSUM_BASE_URL}/{width}/{height}"


def create_default_categories() -> List[ProjectCategory]:
    """Create default project categories"""
    return [
        ProjectCategory(
            id="candid",
            name="candid",
            display_name="Candid",
            description="Natural, unposed moments",
            order=1,
            is_default=True
        ),
        ProjectCategory(
            id="portrait",
            name="portrait",
            display_name="Portrait",
            description="Formal portraits and posed shots",
            order=2,
            is_default=True
        ),
        ProjectCategory(
            id="traditional",
            name="traditional",
            display_name="Traditional",
            description="Traditional ceremony and formal events",
            order=3,
            is_default=True
        ),
    ]


def create_wedding_categories() -> List[ProjectCategory]:
    """Create wedding-specific categories"""
    return [
        ProjectCategory(
            id="getting-ready",
            name="getting-ready",
            display_name="Getting Ready",
            description="Pre-ceremony preparations",
            order=1
        ),
        ProjectCategory(
            id="ceremony",
            name="ceremony",
            display_name="Ceremony",
            description="Wedding ceremony moments",
            order=2
        ),
        ProjectCategory(
            id="reception",
            name="reception",
            display_name="Reception",
            description="Reception and party photos",
            order=3
        ),
        ProjectCategory(
            id="portraits",
            name="portraits",
            display_name="Portraits",
            description="Couple and family portraits",
            order=4
        ),
        ProjectCategory(
            id="details",
            name="details",
            display_name="Details",
            description="Rings, flowers, and other details",
            order=5
        ),
    ]


def create_engagement_categories() -> List[ProjectCategory]:
    """Create engagement-specific categories"""
    return [
        ProjectCategory(
            id="candid",
            name="candid",
            display_name="Candid Moments",
            description="Natural, spontaneous moments",
            order=1
        ),
        ProjectCategory(
            id="portrait",
            name="portrait",
            display_name="Couples Portraits",
            description="Posed couples portraits",
            order=2
        ),
        ProjectCategory(
            id="location",
            name="location",
            display_name="Location Shots",
            description="Beautiful location and scenery",
            order=3
        ),
    ]


def generate_mock_images(project_id: str, categories: List[ProjectCategory], count_per_category: int = 25) -> List[ProjectImage]:
    """Generate mock images for a project"""
    images = []
    
    camera_models = ["Canon EOS R5", "Nikon D850", "Sony A7R IV", "Canon 5D Mark IV", "Nikon Z7"]
    lens_models = ["24-70mm f/2.8", "85mm f/1.4", "50mm f/1.2", "70-200mm f/2.8", "35mm f/1.4"]
    
    # Use more reliable dimensions that work better with Picsum
    valid_dimensions = [
        (800, 600),   # 4:3 ratio - very reliable
        (1200, 800),  # 3:2 ratio - very reliable
        (1600, 900),  # 16:9 ratio - very reliable
        (900, 1200),  # Portrait 3:4 - reduced from 1600 for better reliability
        (600, 800),   # Portrait 4:3 - smaller, more reliable
    ]
    
    for category in categories:
        for i in range(count_per_category):
            image_id = str(uuid.uuid4())
            seed = random.randint(1, 1000)
            
            # Use predefined valid dimensions
            width, height = random.choice(valid_dimensions)
            
            # Create image version
            version = ImageVersion(
                id=f"{image_id}_v1",
                version="v1",
                url=generate_image_url(width, height, seed),
                thumbnail=generate_thumbnail_url(300, 200, seed),
                file_name=f"IMG_{random.randint(1000, 9999)}.jpg",
                uploaded_at=datetime.now() - timedelta(days=random.randint(1, 30)),
                is_latest=True,
                file_size=random.randint(2000000, 8000000),  # 2-8MB
                description=f"Original upload"
            )
            
            # Create image metadata
            metadata = ImageMetadata(
                width=width,
                height=height,
                captured_at=datetime.now() - timedelta(days=random.randint(1, 60)),
                camera=random.choice(camera_models),
                lens=random.choice(lens_models)
            )
            
            # Create project image
            image = ProjectImage(
                id=image_id,
                original_file_name=version.file_name,
                category_id=category.id,
                versions=[version],
                metadata=metadata,
                tags=[],
                is_selected=random.random() < 0.2,  # 20% chance of being selected
                is_favorite=random.random() < 0.1,  # 10% chance of being favorite
                comment_count=random.randint(0, 5),
                created_at=datetime.now() - timedelta(days=random.randint(1, 30)),
                updated_at=datetime.now() - timedelta(days=random.randint(0, 5))
            )
            
            images.append(image)
    
    return images


def generate_mock_data():
    """Generate comprehensive mock data"""
    
    # Create studios
    studio1 = Studio(
        id="studio-001",
        name="Elegant Moments Photography",
        email="contact@elegantmoments.com",
        phone="+1-555-123-4567",
        address="123 Photography Lane, New York, NY 10001",
        logo_url=generate_image_url(200, 200, 1001),
        settings={
            "watermark_enabled": True,
            "default_image_quality": "high",
            "auto_backup": True
        },
        created_at=datetime.now() - timedelta(days=365),
        updated_at=datetime.now() - timedelta(days=30)
    )
    
    studio2 = Studio(
        id="studio-002", 
        name="Timeless Wedding Photography",
        email="hello@timelessweddings.com",
        phone="+1-555-987-6543",
        address="456 Studio Street, Los Angeles, CA 90210",
        logo_url=generate_image_url(200, 200, 1002),
        settings={
            "watermark_enabled": False,
            "default_image_quality": "ultra",
            "auto_backup": True
        },
        created_at=datetime.now() - timedelta(days=200),
        updated_at=datetime.now() - timedelta(days=10)
    )
    
    data_manager.create_studio(studio1)
    data_manager.create_studio(studio2)
    
    # Create users
    users = [
        User(
            id="user-001",
            name="John Smith",
            email="john@elegantmoments.com",
            role=UserRole.STUDIO,
            studio_id="studio-001",
            created_at=datetime.now() - timedelta(days=365),
            updated_at=datetime.now() - timedelta(days=30)
        ),
        User(
            id="user-002",
            name="Sarah Johnson",
            email="sarah@example.com",
            role=UserRole.CLIENT,
            created_at=datetime.now() - timedelta(days=100),
            updated_at=datetime.now() - timedelta(days=10)
        ),
        User(
            id="user-003",
            name="Emma Wilson",
            email="emma@example.com", 
            role=UserRole.CLIENT,
            created_at=datetime.now() - timedelta(days=80),
            updated_at=datetime.now() - timedelta(days=5)
        ),
        User(
            id="user-004",
            name="Michael Chen",
            email="michael@example.com",
            role=UserRole.CLIENT,
            created_at=datetime.now() - timedelta(days=60),
            updated_at=datetime.now() - timedelta(days=2)
        ),
        User(
            id="user-005",
            name="Lisa Martinez",
            email="lisa@timelessweddings.com",
            role=UserRole.STUDIO,
            studio_id="studio-002",
            created_at=datetime.now() - timedelta(days=200),
            updated_at=datetime.now() - timedelta(days=15)
        ),
    ]
    
    for user in users:
        data_manager.create_user(user)
    
    # Create projects with lots of images
    projects = [
        # Large wedding project with 5 categories x 30 images = 150 images
        Project(
            id="proj-001",
            name="Sarah & Michael Wedding",
            description="Beautiful summer wedding at Lake Como with stunning views",
            client_name="Sarah Johnson",
            client_email="sarah@example.com",
            studio_id="studio-001",
            categories=create_wedding_categories(),
            images=[],  # Will be populated below
            settings=ProjectSettings(
                is_password_protected=False,
                allow_downloads=True,
                allow_comments=True
            ),
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now() - timedelta(days=45),
            updated_at=datetime.now() - timedelta(days=5),
            access_url="sarah-michael-wedding-abc123"
        ),
        
        # Medium engagement project with 3 categories x 25 images = 75 images
        Project(
            id="proj-002",
            name="Emma & David Engagement",
            description="Romantic engagement session in Central Park during golden hour",
            client_name="Emma Wilson",
            client_email="emma@example.com",
            studio_id="studio-001",
            categories=create_engagement_categories(),
            images=[],
            settings=ProjectSettings(
                is_password_protected=True,
                password="engagement2024",
                allow_downloads=False,
                allow_comments=True
            ),
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now() - timedelta(days=30),
            updated_at=datetime.now() - timedelta(days=2),
            access_url="emma-david-engagement-xyz789"
        ),
        
        # Another large project with default categories x 35 images = 105 images
        Project(
            id="proj-003",
            name="The Henderson Family Portrait Session",
            description="Annual family portrait session with extended family",
            client_name="Michael Chen",
            client_email="michael@example.com",
            studio_id="studio-002",
            categories=create_default_categories(),
            images=[],
            settings=ProjectSettings(
                is_password_protected=False,
                allow_downloads=True,
                allow_comments=False
            ),
            status=ProjectStatus.COMPLETED,
            created_at=datetime.now() - timedelta(days=60),
            updated_at=datetime.now() - timedelta(days=10),
            access_url="henderson-family-portraits-def456"
        ),
    ]
    
    # Generate images for each project
    for project in projects:
        if project.id == "proj-001":  # Wedding - more images
            project.images = generate_mock_images(project.id, project.categories, 30)
        elif project.id == "proj-002":  # Engagement - medium
            project.images = generate_mock_images(project.id, project.categories, 25)
        else:  # Family - large set
            project.images = generate_mock_images(project.id, project.categories, 35)
        
        data_manager.create_project(project)
    
    # Generate some comments
    sample_comments = [
        "This is absolutely stunning! I love the lighting.",
        "Can we get a high-res version of this one?",
        "Perfect moment captured!",
        "This is definitely going in our album.",
        "Beautiful composition and colors.",
        "Love the emotion in this shot.",
        "Can you edit out the person in the background?",
        "This is our favorite from the session!",
        "The detail in this photo is incredible.",
        "Thank you for capturing this special moment.",
    ]
    
    # Add comments to random images
    all_projects = data_manager.get_projects()
    for project in all_projects:
        for image in random.sample(project.images, min(len(project.images), 20)):  # Comment on up to 20 images per project
            if random.random() < 0.6:  # 60% chance of having a comment
                comment = Comment(
                    id=str(uuid.uuid4()),
                    image_id=image.id,
                    project_id=project.id,
                    user_id="user-002",  # Sarah Johnson commenting
                    user_name="Sarah Johnson",
                    user_role=UserRole.CLIENT,
                    content=random.choice(sample_comments),
                    created_at=datetime.now() - timedelta(days=random.randint(1, 10)),
                    updated_at=datetime.now() - timedelta(days=random.randint(0, 5))
                )
                data_manager.create_comment(comment)
    
    print("Mock data generation complete!")
    print(f"Created {len(data_manager.get_studios())} studios")
    print(f"Created {len(data_manager.get_users())} users")
    print(f"Created {len(data_manager.get_projects())} projects")
    
    # Count total images
    total_images = sum(len(p.images) for p in data_manager.get_projects())
    print(f"Created {total_images} images across all projects")
    
    # Count total comments
    total_comments = len(data_manager.get_comments())
    print(f"Created {total_comments} comments")
    
    # Show project breakdown
    print("\nProject breakdown:")
    for project in data_manager.get_projects():
        print(f"  {project.name}: {len(project.images)} images across {len(project.categories)} categories")


if __name__ == "__main__":
    generate_mock_data()
