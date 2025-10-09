"""Analytics and statistics endpoints."""

from fastapi import APIRouter, Depends

from app.api import deps
from app.core.dependencies import get_current_user, get_data_manager
from app.schemas import Project, Studio, User
from app.services.data_manager import DataManager


router = APIRouter(tags=["Statistics"])


@router.get("/api/projects/{project_id}/stats")
async def get_project_stats(project: Project = Depends(deps.get_project)):
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
async def get_studio_dashboard(
    studio: Studio = Depends(deps.ensure_studio_access),
    data_manager: DataManager = Depends(get_data_manager),
) -> dict:
    stats_data = data_manager.get_studio_stats(studio.id)
    return {
        "studio_id": studio.id,
        "stats": {
            "total_projects": stats_data["total_projects"],
            "active_projects": stats_data["active_projects"],
            "total_images": stats_data["total_images"],
            "total_clients": stats_data["total_clients"],
            "total_comments": stats_data["total_comments"],
        },
        "recent_projects": stats_data["recent_projects"],
    }
