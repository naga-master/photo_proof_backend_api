"""Project management endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api import deps
from app.core.dependencies import get_current_user, get_data_manager
from app.schemas import (
    CreateProjectRequest,
    Project,
    ProjectCategory,
    ProjectListResponse,
    ProjectSettings,
    ProjectStatus,
    User,
    UserRole,
)
from app.services.data_manager import DataManager


router = APIRouter(prefix="/api/projects", tags=["Projects"])


def _default_categories() -> List[ProjectCategory]:
    return [
        ProjectCategory(
            id="candid",
            name="candid",
            display_name="Candid",
            description="Natural, unposed moments",
            order=1,
            is_default=True,
        ),
        ProjectCategory(
            id="portrait",
            name="portrait",
            display_name="Portrait",
            description="Formal portraits and posed shots",
            order=2,
            is_default=True,
        ),
        ProjectCategory(
            id="traditional",
            name="traditional",
            display_name="Traditional",
            description="Traditional ceremony and formal events",
            order=3,
            is_default=True,
        ),
    ]


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    studio_id: Optional[str] = Query(None, description="Filter by studio ID"),
    status: Optional[ProjectStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    data_manager: DataManager = Depends(get_data_manager),
) -> ProjectListResponse:
    projects = data_manager.get_projects(studio_id=studio_id)

    if status:
        projects = [project for project in projects if project.status == status]

    if current_user.role == UserRole.CLIENT:
        projects = [project for project in projects if project.client_email == current_user.email]
    elif current_user.role == UserRole.STUDIO and current_user.studio_id:
        projects = [project for project in projects if project.studio_id == current_user.studio_id]

    return ProjectListResponse(projects=projects, total=len(projects))


@router.get("/{project_id}", response_model=Project)
async def get_project(project: Project = Depends(deps.get_project)) -> Project:
    return project


@router.get("/access/{access_url}", response_model=Project)
async def get_project_by_access_url(
    access_url: str,
    data_manager: DataManager = Depends(get_data_manager),
) -> Project:
    project = data_manager.get_project_by_access_url(access_url)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: CreateProjectRequest,
    current_user: User = Depends(get_current_user),
    data_manager: DataManager = Depends(get_data_manager),
) -> Project:
    if current_user.role != UserRole.STUDIO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only studio users can create projects")

    if not current_user.studio_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Studio assignment missing for current user")

    project_id = str(uuid.uuid4())
    access_url = f"{request.name.lower().replace(' ', '-')}-{str(uuid.uuid4())[:8]}"

    categories = request.categories or _default_categories()

    project = Project(
        id=project_id,
        name=request.name,
        description=request.description,
        client_name=request.client_name,
        client_email=request.client_email,
        studio_id=current_user.studio_id,
        categories=categories,
        images=[],
        settings=ProjectSettings(
            is_password_protected=False,
            allow_downloads=True,
            allow_comments=True,
        ),
        status=ProjectStatus.DRAFT,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        access_url=access_url,
    )

    return data_manager.create_project(project)
