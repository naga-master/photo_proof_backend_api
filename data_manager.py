"""
Data Manager - JSON-based data storage for easy DynamoDB migration

This module handles all data operations using JSON files as the storage layer.
The structure is designed for easy migration to DynamoDB in the future.
"""

import json
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from models import (
    User, Studio, Project, ProjectImage, ProjectCategory, Comment,
    ProjectStatus, UserRole, ImageVersion, ImageMetadata, ProjectSettings
)


class DataManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different data types
        self.users_file = self.data_dir / "users.json"
        self.studios_file = self.data_dir / "studios.json"
        self.projects_file = self.data_dir / "projects.json"
        self.comments_file = self.data_dir / "comments.json"
        
        # Initialize empty files if they don't exist
        self._init_data_files()
        
        # Auto-populate with sample data if empty
        self._ensure_sample_data()
    
    def _init_data_files(self):
        """Initialize empty JSON files if they don't exist"""
        for file_path in [self.users_file, self.studios_file, self.projects_file, self.comments_file]:
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump([], f, indent=2)
    
    def _load_data(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load data from JSON file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_data(self, file_path: Path, data: List[Dict[str, Any]]):
        """Save data to JSON file"""
        # Convert datetime objects to ISO strings for JSON serialization
        serialized_data = []
        for item in data:
            serialized_item = self._serialize_datetime_fields(item)
            serialized_data.append(serialized_item)
        
        with open(file_path, 'w') as f:
            json.dump(serialized_data, f, indent=2, default=str)
    
    def _serialize_datetime_fields(self, obj: Any) -> Any:
        """Convert datetime objects to ISO strings recursively"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._serialize_datetime_fields(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetime_fields(item) for item in obj]
        return obj
    
    def _deserialize_datetime_fields(self, obj: Any, model_class=None) -> Any:
        """Convert ISO strings back to datetime objects"""
        if isinstance(obj, str):
            try:
                return datetime.fromisoformat(obj.replace('Z', '+00:00'))
            except ValueError:
                return obj
        elif isinstance(obj, dict):
            return {k: self._deserialize_datetime_fields(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deserialize_datetime_fields(item) for item in obj]
        return obj
    
    # User operations
    def get_users(self) -> List[User]:
        """Get all users"""
        data = self._load_data(self.users_file)
        return [User(**self._deserialize_datetime_fields(item)) for item in data]
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        users = self.get_users()
        return next((user for user in users if user.id == user_id), None)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        users = self.get_users()
        return next((user for user in users if user.email == email), None)
    
    def create_user(self, user: User) -> User:
        """Create a new user"""
        users = self._load_data(self.users_file)
        user_dict = user.model_dump()
        users.append(user_dict)
        self._save_data(self.users_file, users)
        return user
    
    # Studio operations
    def get_studios(self) -> List[Studio]:
        """Get all studios"""
        data = self._load_data(self.studios_file)
        return [Studio(**self._deserialize_datetime_fields(item)) for item in data]
    
    def get_studio_by_id(self, studio_id: str) -> Optional[Studio]:
        """Get studio by ID"""
        studios = self.get_studios()
        return next((studio for studio in studios if studio.id == studio_id), None)
    
    def create_studio(self, studio: Studio) -> Studio:
        """Create a new studio"""
        studios = self._load_data(self.studios_file)
        studio_dict = studio.model_dump()
        studios.append(studio_dict)
        self._save_data(self.studios_file, studios)
        return studio
    
    # Project operations
    def get_projects(self, studio_id: Optional[str] = None) -> List[Project]:
        """Get all projects, optionally filtered by studio"""
        data = self._load_data(self.projects_file)
        projects = [Project(**self._deserialize_datetime_fields(item)) for item in data]
        
        if studio_id:
            projects = [p for p in projects if p.studio_id == studio_id]
        
        return projects
    
    def get_project_by_id(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        projects = self.get_projects()
        return next((project for project in projects if project.id == project_id), None)
    
    def get_project_by_access_url(self, access_url: str) -> Optional[Project]:
        """Get project by access URL"""
        projects = self.get_projects()
        return next((project for project in projects if project.access_url == access_url), None)
    
    def create_project(self, project: Project) -> Project:
        """Create a new project"""
        projects = self._load_data(self.projects_file)
        project_dict = project.model_dump()
        projects.append(project_dict)
        self._save_data(self.projects_file, projects)
        return project
    
    def update_project(self, project: Project) -> Project:
        """Update an existing project"""
        projects = self._load_data(self.projects_file)
        project_dict = project.model_dump()
        
        for i, p in enumerate(projects):
            if p['id'] == project.id:
                projects[i] = project_dict
                break
        
        self._save_data(self.projects_file, projects)
        return project
    
    def add_image_to_project(self, project_id: str, image: ProjectImage) -> bool:
        """Add an image to a project"""
        project = self.get_project_by_id(project_id)
        if project:
            project.images.append(image)
            project.updated_at = datetime.now()
            self.update_project(project)
            return True
        return False
    
    def add_category_to_project(self, project_id: str, category: ProjectCategory) -> Optional[Project]:
        """Add a category to a project"""
        project = self.get_project_by_id(project_id)
        if project:
            project.categories.append(category)
            project.updated_at = datetime.now()
            return self.update_project(project)
        return None
    
    def update_project_settings(self, project_id: str, settings: ProjectSettings) -> Optional[Project]:
        """Update project settings"""
        project = self.get_project_by_id(project_id)
        if project:
            project.settings = settings
            project.updated_at = datetime.now()
            return self.update_project(project)
        return None
    
    def update_project_image(self, project_id: str, image_id: str, updates: Dict[str, Any]) -> Optional[ProjectImage]:
        """Update a project image"""
        project = self.get_project_by_id(project_id)
        if not project:
            return None
        
        for image in project.images:
            if image.id == image_id:
                # Update fields
                for key, value in updates.items():
                    if hasattr(image, key):
                        setattr(image, key, value)
                image.updated_at = datetime.now()
                
                # Save the updated project
                self.update_project(project)
                return image
        
        return None
    
    # Comment operations
    def get_comments(self, image_id: Optional[str] = None, project_id: Optional[str] = None) -> List[Comment]:
        """Get comments, optionally filtered by image or project"""
        data = self._load_data(self.comments_file)
        comments = [Comment(**self._deserialize_datetime_fields(item)) for item in data]
        
        if image_id:
            comments = [c for c in comments if c.image_id == image_id]
        elif project_id:
            comments = [c for c in comments if c.project_id == project_id]
        
        return comments
    
    def create_comment(self, comment: Comment) -> Comment:
        """Create a new comment"""
        comments = self._load_data(self.comments_file)
        comment_dict = comment.model_dump()
        comments.append(comment_dict)
        self._save_data(self.comments_file, comments)
        
        # Update comment count on the image
        project = self.get_project_by_id(comment.project_id)
        if project:
            for image in project.images:
                if image.id == comment.image_id:
                    image.comment_count += 1
                    self.update_project(project)
                    break
        
        return comment
    
    def _ensure_sample_data(self):
        """Ensure the API has sample data for development"""
        # Check if we already have data
        users = self.get_users()
        projects = self.get_projects()
        
        if len(users) == 0 or len(projects) == 0:
            self._generate_sample_data()
    
    def _generate_sample_data(self):
        """Generate comprehensive sample data"""
        from datetime import datetime, timedelta
        import random
        
        # Create studio user
        studio_user = User(
            id="user-001",
            email="studio@photoproof.com",
            name="Photo Studio",
            role=UserRole.STUDIO,
            studio_id="studio-001",
            created_at=datetime.now() - timedelta(days=30),
            updated_at=datetime.now()
        )
        
        # Create client users
        client_users = [
            User(
                id="user-002",
                email="sarah.johnson@email.com",
                name="Sarah Johnson",
                role=UserRole.CLIENT,
                created_at=datetime.now() - timedelta(days=20),
                updated_at=datetime.now()
            ),
            User(
                id="user-003",
                email="emma.davis@email.com",
                name="Emma Davis",
                role=UserRole.CLIENT,
                created_at=datetime.now() - timedelta(days=15),
                updated_at=datetime.now()
            ),
            User(
                id="user-004",
                email="robert.henderson@email.com",
                name="Robert Henderson",
                role=UserRole.CLIENT,
                created_at=datetime.now() - timedelta(days=10),
                updated_at=datetime.now()
            )
        ]
        
        # Save users
        all_users = [studio_user] + client_users
        for user in all_users:
            self.create_user(user)
        
        # Create studio
        studio = Studio(
            id="studio-001",
            name="Professional Photo Studio",
            owner_id="user-001",
            email="studio@photoproof.com",
            created_at=datetime.now() - timedelta(days=30),
            updated_at=datetime.now()
        )
        self.create_studio(studio)
        
        # Create default categories
        def create_categories(project_type: str):
            if project_type == "wedding":
                return [
                    ProjectCategory(id="cat-all", name="all", display_name="All Photos", order=1, is_default=True),
                    ProjectCategory(id="cat-getting-ready", name="getting-ready", display_name="Getting Ready", order=2),
                    ProjectCategory(id="cat-ceremony", name="ceremony", display_name="Ceremony", order=3),
                    ProjectCategory(id="cat-reception", name="reception", display_name="Reception", order=4),
                    ProjectCategory(id="cat-portraits", name="portraits", display_name="Portraits", order=5),
                    ProjectCategory(id="cat-details", name="details", display_name="Details", order=6)
                ]
            elif project_type == "engagement":
                return [
                    ProjectCategory(id="cat-all", name="all", display_name="All Photos", order=1, is_default=True),
                    ProjectCategory(id="cat-candid", name="candid", display_name="Candid", order=2),
                    ProjectCategory(id="cat-posed", name="posed", display_name="Posed", order=3),
                    ProjectCategory(id="cat-location", name="location", display_name="Location Shots", order=4)
                ]
            else:  # family
                return [
                    ProjectCategory(id="cat-all", name="all", display_name="All Photos", order=1, is_default=True),
                    ProjectCategory(id="cat-group", name="group", display_name="Group Photos", order=2),
                    ProjectCategory(id="cat-individual", name="individual", display_name="Individual Portraits", order=3),
                    ProjectCategory(id="cat-lifestyle", name="lifestyle", display_name="Lifestyle", order=4)
                ]
        
        # Create projects with images
        projects_data = [
            {
                "name": "Sarah & Michael Wedding",
                "description": "Beautiful summer wedding at Lake Como",
                "client_email": "sarah.johnson@email.com",
                "client_name": "Sarah Johnson",
                "type": "wedding",
                "image_count": 150
            },
            {
                "name": "Emma & David Engagement",
                "description": "Romantic engagement session in Central Park",
                "client_email": "emma.davis@email.com",
                "client_name": "Emma Davis",
                "type": "engagement",
                "image_count": 75
            },
            {
                "name": "Henderson Family Portraits",
                "description": "Annual family portraits with three generations",
                "client_email": "robert.henderson@email.com",
                "client_name": "Robert Henderson",
                "type": "family",
                "image_count": 105
            }
        ]
        
        for i, proj_data in enumerate(projects_data):
            project_id = f"project-{i+1:03d}"
            categories = create_categories(proj_data["type"])
            
            # Create images for this project
            images = []
            for img_idx in range(proj_data["image_count"]):
                image_id = f"img-{project_id}-{img_idx+1:03d}"
                
                # Assign to random category (excluding "all")
                non_all_categories = [cat for cat in categories if cat.name != "all"]
                category = random.choice(non_all_categories)
                
                # Create image version
                seed = (i * 1000) + img_idx + 1
                version = ImageVersion(
                    id=f"ver-{image_id}",
                    version="original",
                    url=f"https://picsum.photos/seed/{seed}/800/600",
                    thumbnail=f"https://picsum.photos/seed/{seed}/300/200",
                    file_name=f"{proj_data['type'].upper()}_{img_idx+1:04d}.jpg",
                    uploaded_at=datetime.now() - timedelta(days=random.randint(1, 20)),
                    is_latest=True,
                    file_size=random.randint(1000000, 5000000)
                )
                
                # Create image metadata
                cameras = ["Canon EOS R5", "Nikon D850", "Sony A7R V", "Canon EOS 5D Mark IV"]
                lenses = ["24-70mm f/2.8", "85mm f/1.4", "50mm f/1.2", "70-200mm f/2.8"]
                
                metadata = ImageMetadata(
                    width=3840,
                    height=2560,
                    camera=random.choice(cameras),
                    lens=random.choice(lenses),
                    captured_at=datetime.now() - timedelta(days=random.randint(1, 25))
                )
                
                # Create image
                image = ProjectImage(
                    id=image_id,
                    original_file_name=version.file_name,
                    category_id=category.id,
                    versions=[version],
                    metadata=metadata,
                    tags=[],
                    is_selected=random.random() > 0.8,  # 20% selected
                    is_favorite=random.random() > 0.9,  # 10% favorites
                    comment_count=random.randint(0, 5),
                    created_at=version.uploaded_at,
                    updated_at=version.uploaded_at
                )
                images.append(image)
            
            # Create project
            project = Project(
                id=project_id,
                name=proj_data["name"],
                description=proj_data["description"],
                client_name=proj_data["client_name"],
                client_email=proj_data["client_email"],
                studio_id="studio-001",
                categories=categories,
                images=images,
                settings=ProjectSettings(
                    is_password_protected=False,
                    allow_downloads=True,
                    allow_comments=True
                ),
                status=ProjectStatus.ACTIVE,
                created_at=datetime.now() - timedelta(days=random.randint(15, 30)),
                updated_at=datetime.now() - timedelta(days=random.randint(0, 5)),
                access_url=f"{proj_data['type']}-gallery-{i+1:03d}"
            )
            
            self.create_project(project)
            
            # Create sample comments for some images
            comment_templates = [
                "Love this shot! The lighting is perfect.",
                "This is definitely going in our album.",
                "Could we get this one edited with a warmer tone?",
                "Beautiful moment captured here!",
                "This one is my favorite from the session.",
                "The composition is fantastic.",
                "Perfect expression! We love it.",
                "Could you enhance the colors a bit more?",
                "This captures the emotion perfectly.",
                "Stunning work as always!"
            ]
            
            # Add comments to random images
            commented_images = random.sample(images, min(20, len(images)))
            for image in commented_images:
                for _ in range(image.comment_count):
                    comment = Comment(
                        id=f"comment-{uuid.uuid4()}",
                        image_id=image.id,
                        project_id=project.id,
                        user_id=random.choice(["user-001"] + [u.id for u in client_users]),
                        user_name=random.choice(["Photo Studio", proj_data["client_name"]]),
                        user_role=random.choice([UserRole.STUDIO, UserRole.CLIENT]),
                        content=random.choice(comment_templates),
                        created_at=datetime.now() - timedelta(days=random.randint(0, 10)),
                        updated_at=datetime.now() - timedelta(days=random.randint(0, 10))
                    )
                    self.create_comment(comment)
        
        print("✅ Sample data generated successfully!")
        print(f"   - {len(all_users)} users created")
        print(f"   - {len(projects_data)} projects created")
        print(f"   - {sum(p['image_count'] for p in projects_data)} images created")
        print(f"   - Comments added to random images")

    def get_studio_stats(self, studio_id: str) -> Dict[str, Any]:
        """Get studio statistics WITHOUT loading image data"""
        
        # Load project metadata only (no images)
        projects_data = self._load_data(self.projects_file)
        studio_projects = [p for p in projects_data if p.get('studio_id') == studio_id]
        
        if not studio_projects:
            return {
                "total_projects": 0,
                "active_projects": 0,
                "total_images": 0,
                "total_clients": 0,
                "total_comments": 0,
                "recent_projects": []
            }
        
        # Calculate stats from raw data without deserializing images
        total_projects = len(studio_projects)
        active_projects = len([p for p in studio_projects if p.get('status') == 'active'])
        
        # Count images without loading them
        total_images = sum(len(p.get('images', [])) for p in studio_projects)
        
        # Count unique clients
        unique_clients = len(set(p.get('client_email') for p in studio_projects if p.get('client_email')))
        
        # Count comments without loading image objects
        total_comments = 0
        for project in studio_projects:
            for image_data in project.get('images', []):
                total_comments += image_data.get('comment_count', 0)
        
        # Get recent projects metadata (no images)
        recent_projects = []
        sorted_projects = sorted(studio_projects, 
                               key=lambda p: p.get('updated_at', ''), 
                               reverse=True)[:5]
        
        for project_data in sorted_projects:
            recent_projects.append({
                "id": project_data.get('id'),
                "name": project_data.get('name'),
                "client_name": project_data.get('client_name'),
                "status": project_data.get('status'),
                "image_count": len(project_data.get('images', [])),
                "created_at": project_data.get('created_at'),
                "updated_at": project_data.get('updated_at')
            })
        
        return {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "total_images": total_images,
            "total_clients": unique_clients,
            "total_comments": total_comments,
            "recent_projects": recent_projects
        }


# Global data manager instance
data_manager = DataManager()
