"""Analytics and statistics endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.db import models
from app.db.session import get_db
from app.schemas import ProjectSummary, StudioRead


router = APIRouter(tags=["Statistics"])


@router.get("/api/projects/{project_id}/stats")
def get_project_stats(project: models.Project = Depends(deps.get_project)) -> dict:
    total_images = len(project.images)
    selected_images = len([image for image in project.images if image.is_selected])
    favorite_images = len([image for image in project.images if image.is_favorite])
    total_comments = sum(image.comment_count for image in project.images)

    category_stats = {}
    for category in project.categories:
        category_images = [image for image in project.images if image.category_id == category.id]
        category_stats[category.id] = {
            "name": category.display_name,
            "total_images": len(category_images),
            "selected_images": len([image for image in category_images if image.is_selected]),
            "favorite_images": len([image for image in category_images if image.is_favorite]),
        }

    return {
        "project_id": project.id,
        "total_images": total_images,
        "selected_images": selected_images,
        "favorite_images": favorite_images,
        "total_comments": total_comments,
        "categories": category_stats,
    }


@router.get("/api/studio/{studio_id}/dashboard")
def get_studio_dashboard(
    studio: StudioRead = Depends(deps.ensure_studio_access),
    db: Session = Depends(get_db),
) -> dict:
    total_projects = db.query(models.Project).filter(models.Project.studio_id == studio.id).count()
    active_projects = (
        db.query(models.Project)
        .filter(models.Project.studio_id == studio.id, models.Project.status == "review")
        .count()
    )
    total_images = (
        db.query(models.Image)
        .join(models.Project, models.Project.id == models.Image.project_id)
        .filter(models.Project.studio_id == studio.id)
        .count()
    )
    total_clients = db.query(models.Client).filter(models.Client.studio_id == studio.id).count()
    total_comments = (
        db.query(models.Comment)
        .join(models.Image, models.Image.id == models.Comment.image_id)
        .join(models.Project, models.Project.id == models.Image.project_id)
        .filter(models.Project.studio_id == studio.id)
        .count()
    )

    recent_projects = (
        db.query(models.Project)
        .filter(models.Project.studio_id == studio.id)
        .order_by(models.Project.updated_at.desc())
        .limit(5)
        .all()
    )

    return {
        "studio_id": studio.id,
        "stats": {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "total_images": total_images,
            "total_clients": total_clients,
            "total_comments": total_comments,
        },
        "recent_projects": [ProjectSummary.model_validate(project) for project in recent_projects],
    }
