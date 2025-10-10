"""Project management endpoints backed by the SQL database."""

from __future__ import annotations

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


def _default_category_templates() -> Iterable[CreateCategoryRequest]:
    return [
        CreateCategoryRequest(name="all", display_name="All Photos", is_default=True, order_index=1),
        CreateCategoryRequest(name="favorites", display_name="Favorites", is_default=False, order_index=2),
        CreateCategoryRequest(name="highlights", display_name="Highlights", is_default=False, order_index=3),
    ]


def _serialize_image(image: models.Image) -> ImageRead:
    image_model = ImageRead.model_validate(image)
    versions = [ImageVersionRead.model_validate(version) for version in image.versions]
    tags = [tag.name for tag in image.tags]
    return image_model.model_copy(update={"versions": versions, "tags": tags})


def _project_detail(project: models.Project, include_images: bool = True) -> ProjectDetail:
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
    query = db.query(models.Project).order_by(models.Project.created_at.desc())

    if studio_id:
        query = query.filter(models.Project.studio_id == studio_id)
    elif current_user.studio_id:
        query = query.filter(models.Project.studio_id == current_user.studio_id)

    if status:
        query = query.filter(models.Project.status == status.value)

    projects = query.all()
    summaries = [ProjectSummary.model_validate(project) for project in projects]
    return ProjectListResponse(projects=summaries, total=len(summaries))


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(project: models.Project = Depends(deps.get_project)) -> ProjectDetail:
    return _project_detail(project, include_images=True)


@router.get("/access/{access_url}", response_model=ProjectDetail)
def get_project_by_access_url(access_url: str, db: Session = Depends(get_db)) -> ProjectDetail:
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return _project_detail(project, include_images=True)


@router.post("/", response_model=ProjectDetail, status_code=status.HTTP_201_CREATED)
def create_project(
    request: CreateProjectRequest,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectDetail:
    if current_user.role == UserRole.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only studio users can create projects")

    if not current_user.studio_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Studio assignment required for user")

    client: Optional[models.Client] = None

    client_query = db.query(models.Client).filter(models.Client.studio_id == current_user.studio_id)

    if request.client_id:
        client = client_query.filter(models.Client.id == request.client_id).first()
        if not client:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected client is not available")
    else:
        normalized_email = request.client_email.lower()
        duplicate_filters = [func.lower(models.Client.email) == normalized_email]
        if request.client_phone:
            duplicate_filters.append(models.Client.phone == request.client_phone)

        duplicate = client_query.filter(or_(*duplicate_filters)).first()
        if duplicate:
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
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(project)
    db.flush()

    settings = models.ProjectSettings(project_id=project.id)
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

    return _project_detail(refreshed, include_images=True)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if current_user.role == UserRole.CLIENT or current_user.studio_id != project.studio_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this project")

    db.delete(project)
    db.commit()
