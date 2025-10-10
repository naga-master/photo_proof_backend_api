"""Batch action processing for offline synchronization."""

import uuid
from datetime import datetime
from typing import List, Set

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from app.core.dependencies import get_current_user
from app.db import models
from app.db.session import get_db
from app.schemas import (
    BatchAction,
    BatchActionResult,
    BatchActionsRequest,
    BatchActionsResponse,
    BatchActionType,
    UserRead,
)


router = APIRouter(prefix="/api/actions", tags=["Batch Actions"])


@router.post("/batch", response_model=BatchActionsResponse)
def process_batch_actions(
    request: BatchActionsRequest,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BatchActionsResponse:
    accepted: List[str] = []
    failed: List[BatchActionResult] = []
    processed_actions: Set[str] = set()

    for action in request.actions:
        if action.client_action_id in processed_actions:
            failed.append(
                BatchActionResult(
                    clientActionId=action.client_action_id,
                    reason="Duplicate client_action_id in batch",
                )
            )
            continue

        processed_actions.add(action.client_action_id)

        success = _process_single_action(action, current_user, db)
        if success:
            accepted.append(action.client_action_id)
        else:
            failed.append(
                BatchActionResult(
                    clientActionId=action.client_action_id,
                    reason=f"Failed to process {action.action_type} action",
                )
            )

    return BatchActionsResponse(
        accepted=accepted,
        failed=failed,
        metadata={"processed_count": len(accepted), "total_count": len(request.actions)},
    )


def _process_single_action(action: BatchAction, current_user: UserRead, db: Session) -> bool:
    try:
        if action.action_type == BatchActionType.SELECT:
            return _toggle_boolean_field(action, db, field="is_selected")
        if action.action_type == BatchActionType.FAVORITE:
            return _toggle_boolean_field(action, db, field="is_favorite")
        if action.action_type == BatchActionType.COMMENT:
            return _create_comment(action, current_user, db)
        if action.action_type == BatchActionType.APPROVE:
            return _toggle_tag(action, db, tag_name="approved")
        if action.action_type == BatchActionType.DOWNLOAD:
            return True
        return False
    except Exception:  # noqa: BLE001
        return False


def _fetch_image(action: BatchAction, db: Session) -> models.Image | None:
    if not action.photo_id or not action.project_id:
        return None

    return (
        db.query(models.Image)
        .options(selectinload(models.Image.tags), selectinload(models.Image.project))
        .filter(models.Image.id == action.photo_id, models.Image.project_id == action.project_id)
        .first()
    )


def _toggle_boolean_field(action: BatchAction, db: Session, field: str) -> bool:
    image = _fetch_image(action, db)
    if not image:
        return False

    value = bool(action.payload.get(field, False))
    setattr(image, field, value)
    image.updated_at = datetime.utcnow()
    db.commit()
    return True


def _create_comment(action: BatchAction, current_user: UserRead, db: Session) -> bool:
    image = _fetch_image(action, db)
    if not image:
        return False

    comment_text = action.payload.get("commentText", "").strip()
    if not comment_text:
        return False

    comment = models.Comment(
        id=str(uuid.uuid4()),
        image_id=image.id,
        user_id=current_user.id,
        parent_id=action.payload.get("parentId"),
        content=comment_text,
        resolved=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(comment)

    image.comment_count += 1
    image.updated_at = datetime.utcnow()
    image.project.total_comments = (image.project.total_comments or 0) + 1
    image.project.updated_at = datetime.utcnow()

    db.commit()
    return True


def _toggle_tag(action: BatchAction, db: Session, tag_name: str) -> bool:
    image = _fetch_image(action, db)
    if not image:
        return False

    should_have_tag = bool(action.payload.get("approved", False))
    existing_tags = {tag.name for tag in image.tags}

    if should_have_tag and tag_name not in existing_tags:
        tag = db.query(models.Tag).filter(models.Tag.name == tag_name).first()
        if not tag:
            tag = models.Tag(id=str(uuid.uuid4()), studio_id=image.project.studio_id, name=tag_name)
            db.add(tag)
            db.flush()
        image.tags.append(tag)
    elif not should_have_tag and tag_name in existing_tags:
        image.tags = [tag for tag in image.tags if tag.name != tag_name]

    image.updated_at = datetime.utcnow()
    db.commit()
    return True
