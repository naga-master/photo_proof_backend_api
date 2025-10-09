"""Project category endpoints."""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api import deps
from app.core.dependencies import get_current_user, get_data_manager
from app.schemas import CreateCategoryRequest, Project, ProjectCategory, User, UserRole
from app.services.data_manager import DataManager


router = APIRouter(prefix="/api/projects/{project_id}/categories", tags=["Project Categories"])


@router.get("/", response_model=List[ProjectCategory])
async def list_project_categories(project: Project = Depends(deps.get_project)) -> List[ProjectCategory]:
    return project.categories


@router.post("/", response_model=ProjectCategory, status_code=status.HTTP_201_CREATED)
async def create_project_category(
    request: CreateCategoryRequest,
    project: Project = Depends(deps.get_project),
    current_user: User = Depends(get_current_user),
    data_manager: DataManager = Depends(get_data_manager),
) -> ProjectCategory:
    if current_user.role != UserRole.STUDIO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only studio users can create categories")

    if any(category.name.lower() == request.name.lower() for category in project.categories):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category already exists")

    category = ProjectCategory(
        id=str(uuid.uuid4()),
        name=request.name.lower().replace(" ", "-"),
        display_name=request.display_name,
        description=request.description,
        order=len(project.categories) + 1,
    )

    updated_project = data_manager.add_category_to_project(project.id, category)
    if not updated_project:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to add category")

    return category
