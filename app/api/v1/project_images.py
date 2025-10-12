"""Project image endpoints."""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, text
from sqlalchemy.orm import Session, selectinload

from app.api import deps
from app.core.dependencies import get_current_user
from app.db import models
from app.db.session import get_db
from app.schemas import ImageListResponse, ImageRead, ImageVersionRead, UpdateImageRequest, UserRead, UserRole


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/projects/{project_id}/images", tags=["Project Images"])
gallery_router = APIRouter(prefix="/api/gallery", tags=["Gallery"])


def _serialize_image(image: models.Image) -> ImageRead:
    base = ImageRead.model_validate(image)
    versions = [ImageVersionRead.model_validate(version) for version in image.versions]
    tags = [tag.name for tag in image.tags]
    return base.model_copy(update={"versions": versions, "tags": tags})


def _build_image_query(db: Session, project_id: str, category_id: Optional[str]):
    query = (
        db.query(models.Image)
        .options(selectinload(models.Image.versions), selectinload(models.Image.tags))
        .filter(models.Image.project_id == project_id)
    )

    if category_id:
        normalized = category_id.lower()
        if normalized in {"all", ""}:
            return query
        if normalized == "uncategorized":
            return query.filter(models.Image.category_id.is_(None))
        return query.filter(models.Image.category_id == category_id)

    return query


@router.get("/", response_model=ImageListResponse)
def list_project_images(
    project: models.Project = Depends(deps.get_project),
    category_id: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=200, description="Number of images to return"),
    offset: int = Query(0, ge=0, description="Number of images to skip"),
    db: Session = Depends(get_db),
) -> ImageListResponse:
    logger.debug(
        "Listing project images",
        extra={
            "project_id": project.id,
            "category_id": category_id,
            "limit": limit,
            "offset": offset,
        },
    )
    query = _build_image_query(db, project.id, category_id)
    total = query.count()
    images = (
        query.order_by(models.Image.uploaded_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    serialized = [_serialize_image(image) for image in images]
    logger.debug(
        "Images retrieved",
        extra={"project_id": project.id, "count": len(serialized), "total": total},
    )
    return ImageListResponse(images=serialized, total=total, category_id=category_id)


@router.get("/{image_id}", response_model=ImageRead)
def get_project_image(image: models.Image = Depends(deps.get_project_image)) -> ImageRead:
    logger.debug("Fetching project image", extra={"image_id": image.id})
    return _serialize_image(image)


@router.patch("/{image_id}", response_model=ImageRead)
def update_project_image(
    request: UpdateImageRequest,
    image: models.Image = Depends(deps.get_project_image),
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImageRead:
    logger.debug(
        "Updating project image",
        extra={"image_id": image.id, "user_id": current_user.id},
    )
    project = image.project
    if current_user.role == UserRole.CLIENT or current_user.studio_id != project.studio_id:
        logger.warning(
            "Unauthorized image update attempt",
            extra={"image_id": image.id, "user_id": current_user.id},
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update images")

    if request.category_id:
        category = (
            db.query(models.Category)
            .filter(models.Category.project_id == image.project_id, models.Category.id == request.category_id)
            .first()
        )
        if not category:
            logger.warning(
                "Category not found for image update",
                extra={"category_id": request.category_id, "image_id": image.id},
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found")
        previous_category_id = image.category_id
        image.category_id = category.id
    else:
        previous_category_id = image.category_id

    if request.is_selected is not None:
        image.is_selected = request.is_selected
    if request.is_favorite is not None:
        image.is_favorite = request.is_favorite
    if request.rating is not None:
        image.rating = request.rating

    if request.tags is not None:
        normalized_tags = {tag.strip().lower() for tag in request.tags if tag.strip()}
        tags: List[models.Tag] = []
        for tag_name in normalized_tags:
            tag = db.query(models.Tag).filter(func.lower(models.Tag.name) == tag_name).first()
            if not tag:
                tag = models.Tag(
                    id=str(uuid.uuid4()),
                    studio_id=project.studio_id,
                    name=tag_name,
                    created_at=datetime.utcnow(),
                )
                db.add(tag)
                db.flush()
                logger.debug("Created tag", extra={"tag": tag_name, "studio_id": project.studio_id})
            tags.append(tag)
        image.tags = tags

    image.updated_at = datetime.utcnow()
    project.updated_at = datetime.utcnow()

    db.flush()

    project.total_images = (
        db.query(models.Image).filter(models.Image.project_id == project.id).count()
    )
    project.selected_images = (
        db.query(models.Image).filter(models.Image.project_id == project.id, models.Image.is_selected).count()
    )

    if previous_category_id and previous_category_id != image.category_id:
        previous = db.query(models.Category).filter(models.Category.id == previous_category_id).first()
        if previous:
            previous.image_count = (
                db.query(models.Image).filter(models.Image.category_id == previous.id).count()
            )

    if image.category_id:
        current_category = db.query(models.Category).filter(models.Category.id == image.category_id).first()
        if current_category:
            current_category.image_count = (
                db.query(models.Image).filter(models.Image.category_id == current_category.id).count()
            )

    db.commit()
    db.refresh(image)

    logger.info("Project image updated", extra={"image_id": image.id, "project_id": project.id})
    return _serialize_image(image)


@router.get("/{image_id}/versions", response_model=List[ImageVersionRead])
def list_image_versions(image: models.Image = Depends(deps.get_project_image)) -> List[ImageVersionRead]:
    logger.debug("Listing image versions", extra={"image_id": image.id, "version_count": len(image.versions)})
    return [ImageVersionRead.model_validate(version) for version in image.versions]


@router.post("/{image_id}/versions/{version_id}/restore", response_model=ImageRead)
def restore_image_version(
    version_id: str,
    image: models.Image = Depends(deps.get_project_image),
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImageRead:
    logger.debug(
        "Restoring image version",
        extra={"image_id": image.id, "version_id": version_id, "user_id": current_user.id},
    )

    project = image.project
    if current_user.role == UserRole.CLIENT or current_user.studio_id != project.studio_id:
        logger.warning(
            "Unauthorized version restore attempt",
            extra={"image_id": image.id, "user_id": current_user.id},
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to restore versions")

    version = next((item for item in image.versions if item.id == version_id), None)
    if not version:
        logger.warning(
            "Version not found for restore",
            extra={"image_id": image.id, "version_id": version_id},
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    previous_size = image.file_size_bytes or 0
    new_size = version.file_size_bytes or previous_size

    for existing in image.versions:
        existing.is_current = existing.id == version_id

    image.s3_key_original = version.s3_key
    image.s3_key_thumbnail = version.s3_key
    image.file_size_bytes = new_size
    image.mime_type = version.mime_type or image.mime_type
    image.width = version.width
    image.height = version.height
    image.updated_at = datetime.utcnow()
    image.uploaded_at = datetime.utcnow()

    size_delta = new_size - previous_size
    if size_delta != 0:
        db.execute(
            text(
                "UPDATE projects SET storage_used_bytes = COALESCE(storage_used_bytes, 0) + :delta, updated_at = :updated_at WHERE id = :project_id"
            ),
            {"delta": size_delta, "updated_at": datetime.utcnow(), "project_id": project.id},
        )

    db.commit()
    db.refresh(image)

    logger.info(
        "Restored image version",
        extra={"image_id": image.id, "version_id": version_id, "project_id": project.id},
    )
    return _serialize_image(image)


@gallery_router.get("/{project_id}/{category_id}", response_model=ImageListResponse)
def get_gallery_images(
    project_id: str,
    category_id: str,
    limit: int = Query(200, ge=1, le=500, description="Maximum number of images to return"),
    offset: int = Query(0, ge=0, description="Number of images to skip"),
    db: Session = Depends(get_db),
) -> ImageListResponse:
    logger.debug(
        "Listing gallery images",
        extra={"project_id": project_id, "category_id": category_id, "limit": limit, "offset": offset},
    )
    project = (
        db.query(models.Project)
        .filter(models.Project.id == project_id)
        .first()
    )
    if not project:
        logger.warning("Gallery project not found", extra={"project_id": project_id})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    query = _build_image_query(db, project_id, category_id)
    total = query.count()
    images = (
        query.order_by(models.Image.uploaded_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    serialized = [_serialize_image(image) for image in images]
    logger.debug(
        "Gallery images retrieved",
        extra={"project_id": project_id, "count": len(serialized), "total": total},
    )
    return ImageListResponse(images=serialized, total=total, category_id=category_id)
