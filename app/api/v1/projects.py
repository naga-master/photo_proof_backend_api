"""Project management endpoints backed by the SQL database."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Iterable, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from app.api import deps
from app.core.dependencies import get_current_user
from app.db import models
from app.db.session import get_db
from app.schemas import (
    CreateCategoryRequest,
    CreateProjectRequest,
    ProjectCategoryRead,
    ProjectDetail,
    ProjectListResponse,
    ProjectSettingsRead,
    ProjectStatus,
    ProjectSummary,
    UserRead,
    UserRole,
    ClientRead,
    ImageRead,
    ImageVersionRead,
)


router = APIRouter(prefix="/api/projects", tags=["Projects"])
logger = logging.getLogger(__name__)


def _default_category_templates() -> Iterable[CreateCategoryRequest]:
    return [
        CreateCategoryRequest(name="all", display_name="All Photos", is_default=True, order_index=1),
        CreateCategoryRequest(name="favorites", display_name="Favorites", is_default=False, order_index=2),
        CreateCategoryRequest(name="highlights", display_name="Highlights", is_default=False, order_index=3),
    ]


def _serialize_image(image: models.Image) -> ImageRead:
    # Manually construct data dictionary to avoid Pydantic validation issues with SQLAlchemy metadata
    base_data = {
        "id": image.id,
        "project_id": image.project_id,
        "category_id": image.category_id,
        "original_filename": image.original_filename,
        "s3_key_original": image.s3_key_original,
        "s3_key_thumbnail": image.s3_key_thumbnail,
        "s3_key_preview": image.s3_key_preview,
        "s3_key_print": image.s3_key_print,
        "file_size_bytes": image.file_size_bytes,
        "mime_type": image.mime_type,
        "width": image.width,
        "height": image.height,
        "metadata": {"width": image.width or 0, "height": image.height or 0},  # Create a simple metadata dict
        "captured_at": image.captured_at,
        "camera_make": image.camera_make,
        "camera_model": image.camera_model,
        "focal_length": image.focal_length,
        "shutter_speed": image.shutter_speed,
        "rating": image.rating,
        "is_favorite": image.is_favorite,
        "is_selected": image.is_selected,
        "comment_count": image.comment_count,
        "status": image.status,
        "uploaded_at": image.uploaded_at,
        "updated_at": image.updated_at,
    }
    
    # Serialize versions manually
    versions = []
    for version in image.versions:
        version_data = {
            "id": version.id,
            "image_id": version.image_id,
            "version_name": version.version_name,
            "s3_key": version.s3_key,
            "url": f"/uploads/{version.s3_key}",  # Generate URL from s3_key
            "thumbnail": f"/uploads/{version.s3_key}",  # Generate thumbnail URL from s3_key
            "file_name": version.original_filename,  # Use original_filename as file_name
            "original_filename": version.original_filename,
            "mime_type": version.mime_type,
            "file_size": version.file_size_bytes,  # Use file_size_bytes as file_size
            "file_size_bytes": version.file_size_bytes,
            "width": version.width,
            "height": version.height,
            "checksum": version.checksum,
            "notes": version.notes,
            "is_current": version.is_current,
            "is_latest": version.is_current,  # Use is_current as is_latest
            "uploaded_at": version.created_at,  # Use created_at as uploaded_at
            "created_by": version.created_by,
            "created_at": version.created_at,
        }
        versions.append(ImageVersionRead(**version_data))
    
    # Get tags
    tags = [tag.name for tag in image.tags]
    
    # Add versions and tags to base data
    base_data["versions"] = versions
    base_data["tags"] = tags
    
    return ImageRead(**base_data)


def _project_detail(project: models.Project, include_images: bool = True, db: Optional[Session] = None) -> ProjectDetail:
    # Update total_images count if database session is provided
    if db:
        actual_count = db.query(func.count(models.Image.id)).filter(
            models.Image.project_id == project.id
        ).scalar() or 0
        
        if project.total_images != actual_count:
            project.total_images = actual_count
            db.add(project)
            db.commit()
            logger.debug(
                "Synchronized project total images",
                extra={"project_id": project.id, "total_images": actual_count},
            )
    
    summary = ProjectSummary.model_validate(project)
    categories = [
        ProjectCategoryRead.model_validate(category)
        for category in sorted(project.categories, key=lambda cat: (cat.order_index, cat.created_at))
    ]
    settings = ProjectSettingsRead.model_validate(project.settings) if project.settings else None
    client = ClientRead.model_validate(project.client) if project.client else None
    images: List[ImageRead] = []
    if include_images:
        images = [
            _serialize_image(image)
            for image in sorted(project.images, key=lambda img: img.uploaded_at or img.created_at)
        ]

    detail_payload = summary.model_dump()
    detail_payload.update(
        {
            "delivery_date": project.delivery_date,
            "location": project.location,
            "view_count": project.view_count,
            "last_viewed_at": project.last_viewed_at,
            "client": client,
            "settings": settings,
            "categories": categories,
            "images": images,
        }
    )
    return ProjectDetail(**detail_payload)


@router.get("/", response_model=ProjectListResponse)
def list_projects(
    studio_id: Optional[str] = Query(None, description="Filter by studio ID"),
    status: Optional[ProjectStatus] = Query(None, description="Filter by status"),
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectListResponse:
    logger.debug(
        "Listing projects",
        extra={
            "studio_id": studio_id,
            "status": status.value if status else None,
            "user_id": current_user.id,
        },
    )
    query = db.query(models.Project).order_by(models.Project.created_at.desc())

    if studio_id:
        query = query.filter(models.Project.studio_id == studio_id)
    elif current_user.studio_id:
        query = query.filter(models.Project.studio_id == current_user.studio_id)

    if status:
        query = query.filter(models.Project.status == status.value)

    projects = query.all()
    
    # Recalculate actual image counts for each project
    recalculated = 0
    for project in projects:
        actual_count = db.query(func.count(models.Image.id)).filter(
            models.Image.project_id == project.id
        ).scalar() or 0
        
        if project.total_images != actual_count:
            project.total_images = actual_count
            db.add(project)
            recalculated += 1
    
    db.commit()

    if recalculated:
        logger.debug("Recalculated project image totals", extra={"projects_updated": recalculated})
    
    summaries = [ProjectSummary.model_validate(project) for project in projects]
    logger.debug("Projects retrieved", extra={"count": len(summaries)})
    return ProjectListResponse(projects=summaries, total=len(summaries))


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(project: models.Project = Depends(deps.get_project), db: Session = Depends(get_db)) -> ProjectDetail:
    logger.debug("Fetching project detail", extra={"project_id": project.id})
    return _project_detail(project, include_images=True, db=db)


@router.get("/access/{access_url}", response_model=ProjectDetail)
def get_project_by_access_url(access_url: str, db: Session = Depends(get_db)) -> ProjectDetail:
    logger.debug("Fetching project by access url", extra={"access_url": access_url})
    project = (
        db.query(models.Project)
        .options(
            selectinload(models.Project.categories),
            selectinload(models.Project.images).selectinload(models.Image.versions),
            selectinload(models.Project.images).selectinload(models.Image.tags),
            selectinload(models.Project.settings),
            selectinload(models.Project.client),
        )
        .filter(models.Project.access_url == access_url)
        .first()
    )
    if not project:
        logger.warning("Project not found by access url", extra={"access_url": access_url})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    logger.debug("Project resolved by access url", extra={"project_id": project.id})
    return _project_detail(project, include_images=True, db=db)


@router.post("/", response_model=ProjectDetail, status_code=status.HTTP_201_CREATED)
def create_project(
    request: CreateProjectRequest,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectDetail:
    # Add debug logging for request validation
    logger.debug(
        "Received project creation request",
        extra={
            "user_id": current_user.id, 
            "studio_id": current_user.studio_id,
            "request_type": type(request).__name__,
            "has_name": hasattr(request, 'name'),
            "request_dict": request.model_dump() if hasattr(request, 'model_dump') else str(request)
        }
    )
    
    try:
        project_name = getattr(request, 'name', 'Unknown')
        logger.debug(
            "Creating project",
            extra={"user_id": current_user.id, "studio_id": current_user.studio_id, "name": project_name},
        )
    except Exception as e:
        logger.error(f"Error logging project creation: {e}")
        logger.debug("Creating project - logging failed", extra={"user_id": current_user.id, "studio_id": current_user.studio_id})
    
    if current_user.role == UserRole.CLIENT:
        logger.warning("Client attempted to create project", extra={"user_id": current_user.id})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only studio users can create projects")

    if not current_user.studio_id:
        logger.warning("User missing studio assignment during project creation", extra={"user_id": current_user.id})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Studio assignment required for user")

    client: Optional[models.Client] = None

    client_query = db.query(models.Client).filter(models.Client.studio_id == current_user.studio_id)

    if request.client_id:
        client = client_query.filter(models.Client.id == request.client_id).first()
        if not client:
            logger.warning(
                "Invalid client selection",
                extra={"client_id": request.client_id, "studio_id": current_user.studio_id},
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected client is not available")
    else:
        normalized_email = request.client_email.lower()
        duplicate_filters = [func.lower(models.Client.email) == normalized_email]
        if request.client_phone:
            duplicate_filters.append(models.Client.phone == request.client_phone)

        duplicate = client_query.filter(or_(*duplicate_filters)).first()
        if duplicate:
            logger.warning(
                "Duplicate client detected",
                extra={"email": normalized_email, "studio_id": current_user.studio_id},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email or phone is already associated with an existing client. Choose that client or update the details.",
            )

        client = models.Client(
            id=str(uuid.uuid4()),
            studio_id=current_user.studio_id,
            user_id=None,
            name=request.client_name,
            email=normalized_email,
            phone=request.client_phone,
            status="active",
            total_projects=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(client)
        db.flush()
        logger.info("New client created during project creation", extra={"client_id": client.id})

    project_id = str(uuid.uuid4())
    slug = request.name.lower().replace(" ", "-")
    access_url = f"{slug}-{project_id[:6]}"

    project = models.Project(
        id=project_id,
        studio_id=current_user.studio_id,
        client_id=client.id,
        created_by=current_user.id,
        name=request.name,
        description=request.description,
        project_type=request.project_type,
        shoot_date=request.shoot_date,
        access_url=access_url,
        status=ProjectStatus.DRAFT.value,
        total_images=0,
        selected_images=0,
        total_comments=0,
        storage_used_bytes=0,
        view_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(project)
    db.flush()

    settings = models.ProjectSettings(
        id=str(uuid.uuid4()),
        project_id=project.id,
        is_password_protected=False,
        allow_downloads=True,
        allow_comments=True,
        allow_selections=True,
        allow_favorites=True,
        watermark_enabled=False,
        auto_archive_days=90,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(settings)

    incoming_categories = request.categories or list(_default_category_templates())
    for index, category_req in enumerate(incoming_categories, start=1):
        order_index = category_req.order_index or index
        db.add(
            models.Category(
                id=str(uuid.uuid4()),
                project_id=project.id,
                name=category_req.name,
                display_name=category_req.display_name,
                description=category_req.description,
                order_index=order_index,
                is_default=category_req.is_default,
                image_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

    client.total_projects = (client.total_projects or 0) + 1
    client.updated_at = datetime.utcnow()

    db.commit()

    refreshed = (
        db.query(models.Project)
        .options(
            selectinload(models.Project.categories),
            selectinload(models.Project.images).selectinload(models.Image.versions),
            selectinload(models.Project.images).selectinload(models.Image.tags),
            selectinload(models.Project.settings),
            selectinload(models.Project.client),
        )
        .filter(models.Project.id == project.id)
        .first()
    )

    logger.info("Project created", extra={"project_id": project.id})
    return _project_detail(refreshed, include_images=True)


@router.patch("/{project_id}", response_model=ProjectDetail)
def update_project(
    project_id: str,
    project_update: dict,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Update an existing project."""
    logger.debug("Updating project", extra={"project_id": project_id, "user_id": current_user.id})
    
    # Get the existing project
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        logger.warning("Project not found for update", extra={"project_id": project_id})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Check authorization
    if current_user.role == UserRole.CLIENT or current_user.studio_id != project.studio_id:
        logger.warning(
            "Unauthorized project update attempt",
            extra={"project_id": project_id, "user_id": current_user.id},
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this project")

    # Update project fields
    if "name" in project_update:
        project.name = project_update["name"]
    if "description" in project_update:
        project.description = project_update["description"]
    
    # Update categories if provided
    if "categories" in project_update:
        # Get existing categories
        existing_categories = db.query(models.Category).filter(models.Category.project_id == project_id).all()
        existing_names = {cat.display_name for cat in existing_categories}
        new_names = set(project_update["categories"])
        
        # Remove categories that are no longer needed (but keep their images by reassigning)
        categories_to_remove = existing_names - new_names
        if categories_to_remove:
            # Find the first category to reassign images to (or create a default one)
            default_category = None
            if new_names:
                # Use the first new category as default
                default_category_name = list(new_names)[0]
                default_category = db.query(models.Category).filter(
                    models.Category.project_id == project_id,
                    models.Category.display_name == default_category_name
                ).first()
            
            if not default_category and new_names:
                # Create the first new category to reassign images to
                first_new_category = list(new_names)[0]
                default_category = models.Category(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    name=first_new_category.lower(),
                    display_name=first_new_category,
                    description="",
                    order_index=1,
                    is_default=True
                )
                db.add(default_category)
                db.flush()  # Get the ID
            
            # Reassign images from categories being deleted to the default category
            if default_category:
                for cat_name in categories_to_remove:
                    cat_to_remove = next((cat for cat in existing_categories if cat.display_name == cat_name), None)
                    if cat_to_remove:
                        # Reassign all images to the default category
                        db.query(models.Image).filter(
                            models.Image.category_id == cat_to_remove.id
                        ).update({"category_id": default_category.id})
                        
                        # Now safe to delete the category
                        db.delete(cat_to_remove)
        
        # Add new categories
        for idx, category_name in enumerate(project_update["categories"]):
            # Check if category already exists
            existing_cat = next((cat for cat in existing_categories if cat.display_name == category_name), None)
            if not existing_cat:
                category = models.Category(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    name=category_name.lower(),
                    display_name=category_name,
                    description="",
                    order_index=idx + 1,
                    is_default=(idx == 0)
                )
                db.add(category)
            else:
                # Update order for existing category
                existing_cat.order_index = idx + 1
                existing_cat.is_default = (idx == 0)
    
    # Update settings if provided
    if "settings" in project_update:
        settings_data = project_update["settings"]
        if project.settings:
            # Update existing settings
            if "is_password_protected" in settings_data:
                project.settings.is_password_protected = settings_data["is_password_protected"]
            if "password" in settings_data:
                project.settings.password = settings_data["password"]
            if "allow_downloads" in settings_data:
                project.settings.allow_downloads = settings_data["allow_downloads"]
            if "allow_comments" in settings_data:
                project.settings.allow_comments = settings_data["allow_comments"]
        else:
            # Create new settings
            project.settings = models.ProjectSettings(
                project_id=project_id,
                is_password_protected=settings_data.get("is_password_protected", False),
                password=settings_data.get("password", ""),
                allow_downloads=settings_data.get("allow_downloads", True),
                allow_comments=settings_data.get("allow_comments", True)
            )

    project.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        
        # Refresh with all relationships
        refreshed = (
            db.query(models.Project)
            .options(
                selectinload(models.Project.categories),
                selectinload(models.Project.images).selectinload(models.Image.versions),
                selectinload(models.Project.images).selectinload(models.Image.tags),
                selectinload(models.Project.settings),
                selectinload(models.Project.client),
            )
            .filter(models.Project.id == project_id)
            .first()
        )
        
        logger.info("Project updated", extra={"project_id": project_id})
        return _project_detail(refreshed, include_images=True)
    except Exception as e:
        db.rollback()
        logger.error("Failed to update project", extra={"project_id": project_id, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update project")


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    logger.debug("Deleting project", extra={"project_id": project_id, "user_id": current_user.id})
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        logger.warning("Project not found for deletion", extra={"project_id": project_id})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if current_user.role == UserRole.CLIENT or current_user.studio_id != project.studio_id:
        logger.warning(
            "Unauthorized project deletion attempt",
            extra={"project_id": project_id, "user_id": current_user.id},
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this project")

    db.delete(project)
    db.commit()
    logger.info("Project deleted", extra={"project_id": project_id})
