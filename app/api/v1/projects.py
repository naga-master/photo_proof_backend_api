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


# DEPRECATED: This function references non-existent Image model
# The actual model is Photo in app.db.models.photo
# This function is not currently used and should be removed or rewritten
def _serialize_image(image: models.Photo) -> ImageRead:  # Changed to models.Photo but function is deprecated
    """
    DEPRECATED: Legacy function for Image serialization.
    Current schema uses Photo model, not Image model.
    This function is not used by any active endpoints.
    """
    raise NotImplementedError("Image serialization is deprecated. Use Photo model instead.")


def _project_detail(project: models.Project, include_images: bool = True, db: Optional[Session] = None) -> dict:
    """
    Convert Project model to dictionary matching ProjectDetail schema.
    Note: Returns plain dict instead of ProjectDetail to avoid schema validation issues.
    """
    # Manually create project summary dict matching actual Project model fields
    summary_dict = {
        "id": str(project.id),
        "client_id": str(project.client_id),
        "name": project.title,  # Map title to name
        "total_images": project.photo_count,  # Map photo_count to total_images
        "selected_images": 0,  # Not tracked in current schema
        "total_comments": 0,  # Not tracked at project level
        "storage_used_bytes": 0,  # Not tracked in current schema
        "access_url": None,  # Not in current schema
    }
    
    # Get client data if available
    client = None
    if project.client:
        try:
            client = ClientRead.model_validate(project.client)
        except Exception as e:
            logger.warning(f"Failed to validate client: {e}")
            client = None
    
    # Note: categories, settings, and images relationships don't exist in current schema
    categories = []
    settings = None
    images: List[ImageRead] = []
    
    # Build detail payload
    detail_payload = {
        **summary_dict,
        "delivery_date": None,  # Not in current schema
        "location": None,  # Not in current schema
        "view_count": 0,  # Not in current schema
        "last_viewed_at": None,  # Not in current schema
        "client": client,
        "settings": settings,
        "categories": categories,
        "images": images,
    }
    
    return detail_payload


@router.get("/")
def list_projects(
    studio_id: Optional[str] = Query(None, description="Filter by studio ID"),
    status: Optional[ProjectStatus] = Query(None, description="Filter by status"),
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
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
    
    # Note: Image count syncing removed - Project model uses photo_count, not total_images
    # The photo_count should be updated when photos are added/removed
    
    # Create simplified project summaries matching actual model
    summaries = []
    for project in projects:
        summaries.append({
            "id": str(project.id),
            "studio_id": project.studio_id,
            "client_id": str(project.client_id),
            "title": project.title,
            "shoot_date": project.shoot_date.isoformat() if project.shoot_date else None,
            "cover_photo_id": project.cover_photo_id,
            "photo_count": project.photo_count,
            "is_locked": project.is_locked,
            "layout": project.layout,
            "payment_status": project.payment_status,
            "price": float(project.price) if project.price else None,
            "package_id": project.package_id,
            "status": project.status,
            "has_folders": project.has_folders,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        })
    
    logger.debug("Projects retrieved", extra={"count": len(summaries)})
    return {"projects": summaries, "total": len(summaries)}


@router.get("/{project_id}")
def get_project(project: models.Project = Depends(deps.get_project), db: Session = Depends(get_db)) -> dict:
    logger.debug("Fetching project detail", extra={"project_id": project.id})
    return _project_detail(project, include_images=True, db=db)


@router.get("/access/{access_url}")
def get_project_by_access_url(access_url: str, db: Session = Depends(get_db)) -> dict:
    logger.debug("Fetching project by access url", extra={"access_url": access_url})
    # Note: Project model doesn't have access_url field in current schema
    # This endpoint may need to be updated to use project ID or a different lookup method
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Access URL lookup not implemented in current schema"
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_project(
    request: CreateProjectRequest,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
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
            studio_id=current_user.studio_id,
            user_id=None,
            name=request.client_name,
            email=normalized_email,
            phone=request.client_phone,
            status="active",
        )
        db.add(client)
        db.flush()
        logger.info("New client created during project creation", extra={"client_id": client.id})

    project_id = str(uuid.uuid4())
    slug = request.name.lower().replace(" ", "-")
    access_url = f"{slug}-{project_id[:6]}"

    project = models.Project(
        studio_id=current_user.studio_id,
        client_id=client.id,
        title=request.name,
        shoot_date=request.shoot_date,
        status='draft',
        has_folders=False,
    )
    db.add(project)
    db.flush()

    # Note: ProjectSettings is not in the current schema, skipping for now
    # settings = models.ProjectSettings(
    #     id=str(uuid.uuid4()),
    #     project_id=project.id,
    #     is_password_protected=False,
    #     allow_downloads=True,
    #     allow_comments=True,
    #     allow_selections=True,
    #     allow_favorites=True,
    #     watermark_enabled=False,
    #     auto_archive_days=90,
    #     created_at=datetime.utcnow(),
    #     updated_at=datetime.utcnow(),
    # )
    # db.add(settings)

    # Note: Category is not in the current schema, skipping for now
    # incoming_categories = request.categories or list(_default_category_templates())
    # for index, category_req in enumerate(incoming_categories, start=1):
    #     order_index = category_req.order_index or index
    #     db.add(
    #         models.Category(
    #             id=str(uuid.uuid4()),
    #             project_id=project.id,
    #             name=category_req.name,
    #             display_name=category_req.display_name,
    #             description=category_req.description,
    #             order_index=order_index,
    #             is_default=category_req.is_default,
    #             image_count=0,
    #             created_at=datetime.utcnow(),
    #             updated_at=datetime.utcnow(),
    #         )
    #     )

    # Note: Client.total_projects doesn't exist in current schema
    # client.total_projects = (client.total_projects or 0) + 1
    # client.updated_at = datetime.utcnow()

    db.commit()

    # Refresh the project to get updated data
    db.refresh(project)

    logger.info("Project created", extra={"project_id": project.id})
    
    # Return a simplified project detail that matches our actual model
    return {
        "id": str(project.id),
        "studio_id": project.studio_id,
        "client_id": project.client_id,
        "title": project.title,
        "shoot_date": project.shoot_date.isoformat() if project.shoot_date else None,
        "cover_photo_id": project.cover_photo_id,
        "photo_count": project.photo_count,
        "is_locked": project.is_locked,
        "layout": project.layout,
        "payment_status": project.payment_status,
        "price": float(project.price) if project.price else None,
        "package_id": project.package_id,
        "status": project.status,
        "has_folders": project.has_folders,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


@router.patch("/{project_id}")
def update_project(
    project_id: str,
    project_update: dict,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Update an existing project."""
    logger.debug("Updating project", extra={"project_id": project_id, "user_id": current_user.id})
    
    # Convert project_id to integer (Project model uses Integer ID)
    try:
        project_id_int = int(project_id)
    except ValueError:
        # Check if it's a UUID format (from old frontend mock data)
        if len(project_id) == 36 and project_id.count('-') == 4:
            logger.warning("UUID project ID received (old mock data)", extra={"project_id": project_id})
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found. This appears to be mock data. Please refresh the project list."
            )
        logger.warning("Invalid project ID format", extra={"project_id": project_id})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID format. Expected numeric ID."
        )
    
    # Get the existing project
    project = db.query(models.Project).filter(models.Project.id == project_id_int).first()
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
    if "cover_photo_id" in project_update:
        # Validate that the photo exists and belongs to this project
        photo_id = project_update["cover_photo_id"]
        if photo_id is not None:
            photo = db.query(models.Photo).filter(
                models.Photo.id == photo_id,
                models.Photo.project_id == project_id
            ).first()
            if not photo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cover photo must belong to this project"
                )
        project.cover_photo_id = photo_id
    
    # DEPRECATED: Categories functionality - Category model doesn't exist in current schema
    # The code below references models.Category and models.Image which don't exist
    # This section has been disabled until the schema is updated
    if "categories" in project_update:
        logger.warning("Categories update requested but not implemented in current schema", 
                      extra={"project_id": project_id})
        # Skip categories update - not supported in current schema
    
    # Update settings if provided
    # Note: ProjectSettings model also doesn't exist in current schema
    if "settings" in project_update:
        logger.warning("Settings update requested but not implemented in current schema",
                      extra={"project_id": project_id})
        # Skip settings update - ProjectSettings model doesn't exist
        # The Project model doesn't have a settings relationship

    project.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        
        # Refresh with all relationships
        refreshed = (
            db.query(models.Project)
            .options(
                selectinload(models.Project.client),
                selectinload(models.Project.photos),
                selectinload(models.Project.folders),
            )
            .filter(models.Project.id == project_id_int)
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
    
    # Convert project_id to integer (Project model uses Integer ID)
    try:
        project_id_int = int(project_id)
    except ValueError:
        # Check if it's a UUID format (from old frontend mock data)
        if len(project_id) == 36 and project_id.count('-') == 4:
            logger.warning("UUID project ID received (old mock data)", extra={"project_id": project_id})
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found. This appears to be mock data. Please refresh the project list from the server."
            )
        logger.warning("Invalid project ID format", extra={"project_id": project_id})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID format. Expected numeric ID."
        )
    
    project = db.query(models.Project).filter(models.Project.id == project_id_int).first()
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


@router.get("/{project_id}/folders")
def get_project_folders(
    project_id: str,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all folders for a project.
    
    Returns folders with cover photo information.
    """
    from sqlalchemy.orm import joinedload
    
    logger.debug("Fetching project folders", extra={"project_id": project_id, "user_id": current_user.id})
    
    # Convert project_id to integer
    try:
        project_id_int = int(project_id)
    except ValueError:
        if len(project_id) == 36 and project_id.count('-') == 4:
            logger.warning("UUID project ID received", extra={"project_id": project_id})
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found. This appears to be mock data."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project ID format. Expected numeric ID."
        )
    
    # Get project and verify access
    project = db.query(models.Project).filter(models.Project.id == project_id_int).first()
    
    if not project:
        logger.warning("Project not found", extra={"project_id": project_id})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Authorization check
    if current_user.role == UserRole.CLIENT:
        if project.client_id != current_user.id:
            logger.warning(
                "Unauthorized folder access attempt",
                extra={"project_id": project_id, "user_id": current_user.id}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
    else:  # Studio user
        if project.studio_id != current_user.studio_id:
            logger.warning(
                "Unauthorized folder access attempt",
                extra={"project_id": project_id, "user_id": current_user.id}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
    
    # Get folders with cover photos
    folders = (
        db.query(models.Folder)
        .options(joinedload(models.Folder.cover_photo))
        .filter(models.Folder.project_id == project_id_int)
        .order_by(models.Folder.order_index, models.Folder.created_at)
        .all()
    )
    
    # Format response
    folder_list = []
    for folder in folders:
        cover_photo_src = None
        if folder.cover_photo:
            cover_photo_src = f"/uploads/{folder.cover_photo.storage_path}"
        
        folder_list.append({
            "id": folder.id,
            "name": folder.name,
            "project_id": folder.project_id,
            "photo_count": folder.photo_count if hasattr(folder, 'photo_count') else 0,
            "cover_photo_id": folder.cover_photo_id,
            "cover_photo_src": cover_photo_src,
            "order_index": folder.order_index if hasattr(folder, 'order_index') else 0,
            "created_at": folder.created_at.isoformat() if folder.created_at else None,
            "updated_at": folder.updated_at.isoformat() if folder.updated_at else None,
        })
    
    logger.info("Project folders retrieved", extra={"project_id": project_id, "folder_count": len(folder_list)})
    
    return {
        "folders": folder_list,
        "total": len(folder_list)
    }
