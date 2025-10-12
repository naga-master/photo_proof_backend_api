"""Project category endpoints."""

import logging
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core.dependencies import get_current_user
from app.db import models
from app.db.session import get_db
from app.schemas import CreateCategoryRequest, ProjectCategoryRead, UserRead, UserRole


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/projects/{project_id}/categories", tags=["Project Categories"])


@router.get("/", response_model=List[ProjectCategoryRead])
def list_project_categories(project: models.Project = Depends(deps.get_project)) -> List[ProjectCategoryRead]:
    logger.debug("Listing categories", extra={"project_id": project.id})
    return [
        ProjectCategoryRead.model_validate(category)
        for category in sorted(project.categories, key=lambda cat: (cat.order_index, cat.created_at))
    ]


@router.post("/", response_model=ProjectCategoryRead, status_code=status.HTTP_201_CREATED)
def create_project_category(
    request: CreateCategoryRequest,
    project: models.Project = Depends(deps.get_project),
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectCategoryRead:
    logger.debug(
        "Creating project category",
        extra={"project_id": project.id, "user_id": current_user.id, "name": request.name},
    )
    if current_user.role == UserRole.CLIENT or current_user.studio_id != project.studio_id:
        logger.warning(
            "Unauthorized category creation",
            extra={"project_id": project.id, "user_id": current_user.id},
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to add categories")

    if any(category.name.lower() == request.name.lower() for category in project.categories):
        logger.warning(
            "Duplicate category name",
            extra={"project_id": project.id, "name": request.name},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category already exists")

    order_index = request.order_index or (len(project.categories) + 1)
    category = models.Category(
        id=str(uuid.uuid4()),
        project_id=project.id,
        name=request.name.lower().replace(" ", "-"),
        display_name=request.display_name,
        description=request.description,
        order_index=order_index,
        is_default=request.is_default,
        image_count=0,
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    logger.info("Project category created", extra={"project_id": project.id, "category_id": category.id})
    return ProjectCategoryRead.model_validate(category)
