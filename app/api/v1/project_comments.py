"""Project image comment endpoints backed by SQLite storage."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.api import deps
from app.core.dependencies import get_current_user
from app.db import models
from app.db.session import get_db
from app.schemas import CommentListResponse, CommentRead, CreateCommentRequest, UserRead


router = APIRouter(
    prefix="/api/projects/{project_id}/images/{image_id}/comments",
    tags=["Project Comments"],
)


@router.get("/", response_model=CommentListResponse)
def list_image_comments(
    image: models.Image = Depends(deps.get_project_image),
    db: Session = Depends(get_db),
) -> CommentListResponse:
    comments = (
        db.query(models.Comment)
        .options(selectinload(models.Comment.user))
        .filter(models.Comment.image_id == image.id)
        .order_by(models.Comment.created_at.asc())
        .all()
    )

    serialized = [
        CommentRead.model_validate(comment).model_copy(
            update={
                "user_name": comment.user.name if comment.user else None,
                "user_role": comment.user.role if comment.user else None,
            }
        )
        for comment in comments
    ]
    return CommentListResponse(comments=serialized, total=len(serialized), image_id=image.id)


@router.post("/", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
def create_image_comment(
    request: CreateCommentRequest,
    image: models.Image = Depends(deps.get_project_image),
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CommentRead:
    comment = models.Comment(
        id=str(uuid.uuid4()),
        image_id=image.id,
        user_id=current_user.id,
        parent_id=request.parent_id,
        content=request.content,
        resolved=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(comment)

    image.comment_count += 1
    image.updated_at = datetime.utcnow()
    image.project.total_comments += 1
    image.project.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(comment)

    return CommentRead.model_validate(comment).model_copy(
        update={"user_name": current_user.name, "user_role": current_user.role}
    )
