"""JSON-backed data persistence for the Photo Proof API."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.schemas import (
    Comment,
    ImageMetadata,
    ImageVersion,
    Project,
    ProjectCategory,
    ProjectImage,
    ProjectSettings,
    ProjectStatus,
    Studio,
    User,
    UserRole,
)


class DataManager:
    def __init__(self, data_dir: str = "data") -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        self.users_file = self.data_dir / "users.json"
        self.studios_file = self.data_dir / "studios.json"
        self.projects_file = self.data_dir / "projects.json"
        self.comments_file = self.data_dir / "comments.json"

        self._init_data_files()
        self._ensure_sample_data()

    def _init_data_files(self) -> None:
        for file_path in [self.users_file, self.studios_file, self.projects_file, self.comments_file]:
            if not file_path.exists():
                with open(file_path, "w", encoding="utf-8") as file_object:
                    json.dump([], file_object, indent=2)

    def _load_data(self, file_path: Path) -> List[Dict[str, Any]]:
        try:
            with open(file_path, "r", encoding="utf-8") as file_object:
                return json.load(file_object)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_data(self, file_path: Path, data: List[Dict[str, Any]]) -> None:
        serialised = [self._serialize_datetime_fields(item) for item in data]
        with open(file_path, "w", encoding="utf-8") as file_object:
            json.dump(serialised, file_object, indent=2, default=str)

    def _serialize_datetime_fields(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {key: self._serialize_datetime_fields(value) for key, value in obj.items()}
        if isinstance(obj, list):
            return [self._serialize_datetime_fields(item) for item in obj]
        return obj

    def _deserialize_datetime_fields(self, obj: Any) -> Any:
        if isinstance(obj, str):
            try:
                return datetime.fromisoformat(obj.replace("Z", "+00:00"))
            except ValueError:
                return obj
        if isinstance(obj, dict):
            return {key: self._deserialize_datetime_fields(value) for key, value in obj.items()}
        if isinstance(obj, list):
            return [self._deserialize_datetime_fields(item) for item in obj]
        return obj

    def get_users(self) -> List[User]:
        data = self._load_data(self.users_file)
        return [User(**self._deserialize_datetime_fields(item)) for item in data]

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return next((user for user in self.get_users() if user.id == user_id), None)

    def get_user_by_email(self, email: str) -> Optional[User]:
        return next((user for user in self.get_users() if user.email == email), None)

    def create_user(self, user: User) -> User:
        users = self._load_data(self.users_file)
        users.append(user.model_dump())
        self._save_data(self.users_file, users)
        return user

    def get_studios(self) -> List[Studio]:
        data = self._load_data(self.studios_file)
        return [Studio(**self._deserialize_datetime_fields(item)) for item in data]

    def get_studio_by_id(self, studio_id: str) -> Optional[Studio]:
        return next((studio for studio in self.get_studios() if studio.id == studio_id), None)

    def create_studio(self, studio: Studio) -> Studio:
        studios = self._load_data(self.studios_file)
        studios.append(studio.model_dump())
        self._save_data(self.studios_file, studios)
        return studio

    def get_projects(self, studio_id: Optional[str] = None) -> List[Project]:
        data = self._load_data(self.projects_file)
        projects = [Project(**self._deserialize_datetime_fields(item)) for item in data]
        if studio_id:
            projects = [project for project in projects if project.studio_id == studio_id]
        return projects

    def get_project_by_id(self, project_id: str) -> Optional[Project]:
        return next((project for project in self.get_projects() if project.id == project_id), None)

    def get_project_by_access_url(self, access_url: str) -> Optional[Project]:
        return next((project for project in self.get_projects() if project.access_url == access_url), None)

    def create_project(self, project: Project) -> Project:
        projects = self._load_data(self.projects_file)
        projects.append(project.model_dump())
        self._save_data(self.projects_file, projects)
        return project

    def delete_project(self, project_id: str) -> bool:
        """Delete a project by ID. Returns True if deleted, False if not found."""
        projects = self._load_data(self.projects_file)
        original_length = len(projects)
        projects = [p for p in projects if p.get("id") != project_id]
        
        if len(projects) < original_length:
            self._save_data(self.projects_file, projects)
            return True
        return False

    def update_project(self, project: Project) -> Project:
        projects = self._load_data(self.projects_file)
        project_dict = project.model_dump()
        for index, existing in enumerate(projects):
            if existing["id"] == project.id:
                projects[index] = project_dict
                break
        self._save_data(self.projects_file, projects)
        return project

    def add_image_to_project(self, project_id: str, image: ProjectImage) -> bool:
        project = self.get_project_by_id(project_id)
        if not project:
            return False
        project.images.append(image)
        project.updated_at = datetime.now()
        self.update_project(project)
        return True

    def add_category_to_project(self, project_id: str, category: ProjectCategory) -> Optional[Project]:
        project = self.get_project_by_id(project_id)
        if not project:
            return None
        project.categories.append(category)
        project.updated_at = datetime.now()
        return self.update_project(project)

    def update_project_settings(self, project_id: str, settings: ProjectSettings) -> Optional[Project]:
        project = self.get_project_by_id(project_id)
        if not project:
            return None
        project.settings = settings
        project.updated_at = datetime.now()
        return self.update_project(project)

    def update_project_image(self, project_id: str, image_id: str, updates: Dict[str, Any]) -> Optional[ProjectImage]:
        project = self.get_project_by_id(project_id)
        if not project:
            return None
        for image in project.images:
            if image.id == image_id:
                for key, value in updates.items():
                    if hasattr(image, key):
                        setattr(image, key, value)
                image.updated_at = datetime.now()
                self.update_project(project)
                return image
        return None

    def get_comments(self, image_id: Optional[str] = None, project_id: Optional[str] = None) -> List[Comment]:
        data = self._load_data(self.comments_file)
        comments = [Comment(**self._deserialize_datetime_fields(item)) for item in data]
        if image_id:
            comments = [comment for comment in comments if comment.image_id == image_id]
        elif project_id:
            comments = [comment for comment in comments if comment.project_id == project_id]
        return comments

    def create_comment(self, comment: Comment) -> Comment:
        comments = self._load_data(self.comments_file)
        comments.append(comment.model_dump())
        self._save_data(self.comments_file, comments)

        project = self.get_project_by_id(comment.project_id)
        if project:
            for image in project.images:
                if image.id == comment.image_id:
                    image.comment_count += 1
                    self.update_project(project)
                    break

        return comment

    def _ensure_sample_data(self) -> None:
        users = self.get_users()
        projects = self.get_projects()
        if users and projects:
            return
        self._generate_sample_data()

    def _generate_sample_data(self) -> None:
        import random

        studio_user = User(
            id="user-001",
            email="studio@photoproof.com",
            name="Photo Studio",
            role=UserRole.STUDIO,
            studio_id="studio-001",
            created_at=datetime.now() - timedelta(days=30),
            updated_at=datetime.now(),
        )

        client_users = [
            User(
                id="user-002",
                email="sarah.johnson@email.com",
                name="Sarah Johnson",
                role=UserRole.CLIENT,
                created_at=datetime.now() - timedelta(days=20),
                updated_at=datetime.now(),
            ),
            User(
                id="user-003",
                email="emma.davis@email.com",
                name="Emma Davis",
                role=UserRole.CLIENT,
                created_at=datetime.now() - timedelta(days=15),
                updated_at=datetime.now(),
            ),
            User(
                id="user-004",
                email="robert.henderson@email.com",
                name="Robert Henderson",
                role=UserRole.CLIENT,
                created_at=datetime.now() - timedelta(days=10),
                updated_at=datetime.now(),
            ),
        ]

        for user in [studio_user, *client_users]:
            self.create_user(user)

        studio = Studio(
            id="studio-001",
            name="Professional Photo Studio",
            owner_id="user-001",
            email="studio@photoproof.com",
            created_at=datetime.now() - timedelta(days=30),
            updated_at=datetime.now(),
        )
        self.create_studio(studio)

        def create_categories(project_type: str) -> List[ProjectCategory]:
            if project_type == "wedding":
                return [
                    ProjectCategory(id="cat-all", name="all", display_name="All Photos", order=1, is_default=True),
                    ProjectCategory(id="cat-getting-ready", name="getting-ready", display_name="Getting Ready", order=2),
                    ProjectCategory(id="cat-ceremony", name="ceremony", display_name="Ceremony", order=3),
                    ProjectCategory(id="cat-reception", name="reception", display_name="Reception", order=4),
                    ProjectCategory(id="cat-portraits", name="portraits", display_name="Portraits", order=5),
                    ProjectCategory(id="cat-details", name="details", display_name="Details", order=6),
                ]
            if project_type == "engagement":
                return [
                    ProjectCategory(id="cat-all", name="all", display_name="All Photos", order=1, is_default=True),
                    ProjectCategory(id="cat-candid", name="candid", display_name="Candid", order=2),
                    ProjectCategory(id="cat-posed", name="posed", display_name="Posed", order=3),
                    ProjectCategory(id="cat-location", name="location", display_name="Location Shots", order=4),
                ]
            return [
                ProjectCategory(id="cat-all", name="all", display_name="All Photos", order=1, is_default=True),
                ProjectCategory(id="cat-group", name="group", display_name="Group Photos", order=2),
                ProjectCategory(id="cat-individual", name="individual", display_name="Individual Portraits", order=3),
                ProjectCategory(id="cat-lifestyle", name="lifestyle", display_name="Lifestyle", order=4),
            ]

        projects_data = [
            {
                "name": "Sarah & Michael Wedding",
                "description": "Beautiful summer wedding at Lake Como",
                "client_email": "sarah.johnson@email.com",
                "client_name": "Sarah Johnson",
                "type": "wedding",
                "image_count": 150,
            },
            {
                "name": "Emma & David Engagement",
                "description": "Romantic engagement session in Central Park",
                "client_email": "emma.davis@email.com",
                "client_name": "Emma Davis",
                "type": "engagement",
                "image_count": 75,
            },
            {
                "name": "Henderson Family Portraits",
                "description": "Annual family portraits with three generations",
                "client_email": "robert.henderson@email.com",
                "client_name": "Robert Henderson",
                "type": "family",
                "image_count": 105,
            },
        ]

        for index, project_data in enumerate(projects_data):
            project_id = f"project-{index + 1:03d}"
            categories = create_categories(project_data["type"])

            images: List[ProjectImage] = []
            for image_index in range(project_data["image_count"]):
                image_id = f"img-{project_id}-{image_index + 1:03d}"
                non_all_categories = [category for category in categories if category.name != "all"]
                category = random.choice(non_all_categories)

                seed = (index * 1000) + image_index + 1
                version = ImageVersion(
                    id=f"ver-{image_id}",
                    version="original",
                    url=f"https://picsum.photos/seed/{seed}/800/600",
                    thumbnail=f"https://picsum.photos/seed/{seed}/300/200",
                    file_name=f"{project_data['type'].upper()}_{image_index + 1:04d}.jpg",
                    uploaded_at=datetime.now() - timedelta(days=random.randint(1, 20)),
                    is_latest=True,
                    file_size=random.randint(1_000_000, 5_000_000),
                )

                cameras = ["Canon EOS R5", "Nikon D850", "Sony A7R V", "Canon EOS 5D Mark IV"]
                lenses = ["24-70mm f/2.8", "85mm f/1.4", "50mm f/1.2", "70-200mm f/2.8"]

                metadata = ImageMetadata(
                    width=3840,
                    height=2560,
                    camera=random.choice(cameras),
                    lens=random.choice(lenses),
                    captured_at=datetime.now() - timedelta(days=random.randint(1, 25)),
                )

                image = ProjectImage(
                    id=image_id,
                    original_file_name=version.file_name,
                    category_id=category.id,
                    versions=[version],
                    metadata=metadata,
                    tags=[],
                    is_selected=random.random() > 0.8,
                    is_favorite=random.random() > 0.9,
                    comment_count=random.randint(0, 5),
                    created_at=version.uploaded_at,
                    updated_at=version.uploaded_at,
                )
                images.append(image)

            project = Project(
                id=project_id,
                name=project_data["name"],
                description=project_data["description"],
                client_name=project_data["client_name"],
                client_email=project_data["client_email"],
                studio_id="studio-001",
                categories=categories,
                images=images,
                settings=ProjectSettings(
                    is_password_protected=False,
                    allow_downloads=True,
                    allow_comments=True,
                ),
                status=ProjectStatus.ACTIVE,
                created_at=datetime.now() - timedelta(days=random.randint(15, 30)),
                updated_at=datetime.now() - timedelta(days=random.randint(0, 5)),
                access_url=f"{project_data['type']}-gallery-{index + 1:03d}",
            )

            self.create_project(project)

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
                "Stunning work as always!",
            ]

            commented_images = random.sample(images, min(20, len(images)))
            for image in commented_images:
                for _ in range(image.comment_count):
                    comment = Comment(
                        id=f"comment-{uuid.uuid4()}",
                        image_id=image.id,
                        project_id=project.id,
                        user_id=random.choice(["user-001", *[user.id for user in client_users]]),
                        user_name=random.choice(["Photo Studio", project_data["client_name"]]),
                        user_role=random.choice([UserRole.STUDIO, UserRole.CLIENT]),
                        content=random.choice(comment_templates),
                        created_at=datetime.now() - timedelta(days=random.randint(0, 10)),
                        updated_at=datetime.now() - timedelta(days=random.randint(0, 10)),
                    )
                    self.create_comment(comment)

        print("✅ Sample data generated successfully!")
        print(f"   - {1 + len(client_users)} users created")
        print(f"   - {len(projects_data)} projects created")
        print(f"   - {sum(project['image_count'] for project in projects_data)} images created")

    def get_studio_stats(self, studio_id: str) -> Dict[str, Any]:
        projects_data = self._load_data(self.projects_file)
        studio_projects = [project for project in projects_data if project.get("studio_id") == studio_id]

        if not studio_projects:
            return {
                "total_projects": 0,
                "active_projects": 0,
                "total_images": 0,
                "total_clients": 0,
                "total_comments": 0,
                "recent_projects": [],
            }

        total_projects = len(studio_projects)
        active_projects = len([project for project in studio_projects if project.get("status") == ProjectStatus.ACTIVE.value])
        total_images = sum(len(project.get("images", [])) for project in studio_projects)
        unique_clients = len({project.get("client_email") for project in studio_projects if project.get("client_email")})

        total_comments = 0
        for project in studio_projects:
            for image in project.get("images", []):
                total_comments += image.get("comment_count", 0)

        recent_projects: List[Dict[str, Any]] = []
        sorted_projects = sorted(studio_projects, key=lambda project: project.get("updated_at", ""), reverse=True)[:5]

        for project_data in sorted_projects:
            recent_projects.append(
                {
                    "id": project_data.get("id"),
                    "name": project_data.get("name"),
                    "client_name": project_data.get("client_name"),
                    "status": project_data.get("status"),
                    "image_count": len(project_data.get("images", [])),
                    "created_at": project_data.get("created_at"),
                    "updated_at": project_data.get("updated_at"),
                }
            )

        return {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "total_images": total_images,
            "total_clients": unique_clients,
            "total_comments": total_comments,
            "recent_projects": recent_projects,
        }


__all__ = ["DataManager"]
