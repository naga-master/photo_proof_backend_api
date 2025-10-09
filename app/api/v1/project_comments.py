"""Project image comment endpoints."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.api import deps
from app.core.dependencies import get_current_user, get_data_manager
from app.schemas import (
    Comment,
    CommentListResponse,
    CreateCommentRequest,
    Project,
    ProjectImage,
    User,
)
from app.services.data_manager import DataManager


router = APIRouter(
    prefix="/api/projects/{project_id}/images/{image_id}/comments",
    tags=["Project Comments"],
)


@router.get("/", response_model=CommentListResponse)
async def list_image_comments(
    project: Project = Depends(deps.get_project),
    image: ProjectImage = Depends(deps.get_project_image),
    data_manager: DataManager = Depends(get_data_manager),
) -> CommentListResponse:
    comments = data_manager.get_comments(image_id=image.id)
    return CommentListResponse(comments=comments, total=len(comments), image_id=image.id)


@router.post("/", response_model=Comment, status_code=status.HTTP_201_CREATED)
async def create_image_comment(
    request: CreateCommentRequest,
    project: Project = Depends(deps.get_project),
    image: ProjectImage = Depends(deps.get_project_image),
    current_user: User = Depends(get_current_user),
    data_manager: DataManager = Depends(get_data_manager),
) -> Comment:
    comment = Comment(
        id=str(uuid.uuid4()),
        image_id=image.id,
        project_id=project.id,
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role,
        content=request.content,
        parent_id=request.parent_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    created_comment = data_manager.create_comment(comment)
    if not created_comment:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create comment")

    return created_comment
