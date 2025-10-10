"""Project category endpoints."""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core.dependencies import get_current_user
from app.db import models
from app.db.session import get_db
from app.schemas import CreateCategoryRequest, ProjectCategoryRead, UserRead, UserRole


router = APIRouter(prefix="/api/projects/{project_id}/categories", tags=["Project Categories"])


@router.get("/", response_model=List[ProjectCategoryRead])
def list_project_categories(project: models.Project = Depends(deps.get_project)) -> List[ProjectCategoryRead]:
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
    if current_user.role == UserRole.CLIENT or current_user.studio_id != project.studio_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to add categories")

    if any(category.name.lower() == request.name.lower() for category in project.categories):
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

    return ProjectCategoryRead.model_validate(category)
