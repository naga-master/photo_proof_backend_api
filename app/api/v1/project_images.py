"""Project image endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api import deps
from app.core.dependencies import get_current_user, get_data_manager
from app.schemas import ImageListResponse, Project, ProjectImage, UpdateImageRequest, User
from app.services.data_manager import DataManager


router = APIRouter(prefix="/api/projects/{project_id}/images", tags=["Project Images"])


@router.get("/", response_model=ImageListResponse)
async def list_project_images(
    project: Project = Depends(deps.get_project),
    category_id: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=200, description="Number of images to return"),
    offset: int = Query(0, ge=0, description="Number of images to skip"),
) -> ImageListResponse:
    images = project.images

    if category_id:
        images = [image for image in images if image.category_id == category_id]

    total = len(images)
    paginated_images = images[offset : offset + limit]

    return ImageListResponse(images=paginated_images, total=total, category_id=category_id or "all")


@router.get("/{image_id}", response_model=ProjectImage)
async def get_project_image(image: ProjectImage = Depends(deps.get_project_image)) -> ProjectImage:
    return image


@router.patch("/{image_id}", response_model=ProjectImage)
async def update_project_image(
    request: UpdateImageRequest,
    project: Project = Depends(deps.get_project),
    image: ProjectImage = Depends(deps.get_project_image),
    _current_user: User = Depends(get_current_user),
    data_manager: DataManager = Depends(get_data_manager),
) -> ProjectImage:
    updates = {}
    if request.is_selected is not None:
        updates["is_selected"] = request.is_selected
    if request.is_favorite is not None:
        updates["is_favorite"] = request.is_favorite
    if request.tags is not None:
        updates["tags"] = request.tags

    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No updates provided")

    updated_image = data_manager.update_project_image(project.id, image.id, updates)
    if not updated_image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image or project not found")

    return updated_image
