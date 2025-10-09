"""Batch action processing for offline synchronization."""

import uuid
from datetime import datetime
from typing import List, Set

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user, get_data_manager
from app.schemas import (
    BatchAction,
    BatchActionResult,
    BatchActionsRequest,
    BatchActionsResponse,
    BatchActionType,
    Comment,
    Project,
    User,
)
from app.services.data_manager import DataManager


router = APIRouter(prefix="/api/actions", tags=["Batch Actions"])


@router.post("/batch", response_model=BatchActionsResponse)
async def process_batch_actions(
    request: BatchActionsRequest,
    current_user: User = Depends(get_current_user),
    data_manager: DataManager = Depends(get_data_manager),
) -> BatchActionsResponse:
    print(f"🔄 Processing batch of {len(request.actions)} actions")

    accepted: List[str] = []
    failed: List[BatchActionResult] = []
    processed_actions: Set[str] = set()

    for action in request.actions:
        try:
            if action.client_action_id in processed_actions:
                failed.append(
                    BatchActionResult(
                        clientActionId=action.client_action_id,
                        reason="Duplicate client_action_id in batch",
                    )
                )
                continue

            processed_actions.add(action.client_action_id)

            success = await _process_single_action(action, current_user, data_manager)

            if success:
                accepted.append(action.client_action_id)
                print(f"✅ Processed {action.action_type} action: {action.client_action_id}")
            else:
                failed.append(
                    BatchActionResult(
                        clientActionId=action.client_action_id,
                        reason=f"Failed to process {action.action_type} action",
                    )
                )
                print(f"❌ Failed {action.action_type} action: {action.client_action_id}")
        except Exception as exc:  # noqa: BLE001
            failed.append(BatchActionResult(clientActionId=action.client_action_id, reason=str(exc)))
            print(f"💥 Error processing action {action.client_action_id}: {exc}")

    response = BatchActionsResponse(
        accepted=accepted,
        failed=failed,
        metadata={"processed_count": len(accepted), "total_count": len(request.actions)},
    )

    print(f"📊 Batch complete: {len(accepted)} accepted, {len(failed)} failed")
    return response


async def _process_single_action(
    action: BatchAction,
    current_user: User,
    data_manager: DataManager,
) -> bool:
    try:
        if action.action_type == BatchActionType.SELECT:
            return _process_select_action(action, data_manager)
        if action.action_type == BatchActionType.FAVORITE:
            return _process_favorite_action(action, data_manager)
        if action.action_type == BatchActionType.COMMENT:
            return _process_comment_action(action, current_user, data_manager)
        if action.action_type == BatchActionType.APPROVE:
            return _process_approve_action(action, data_manager)
        if action.action_type == BatchActionType.DOWNLOAD:
            return _process_download_action(action, current_user)
        print(f"⚠️ Unknown action type: {action.action_type}")
        return False
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Error in _process_single_action: {exc}")
        return False


def _process_select_action(action: BatchAction, data_manager: DataManager) -> bool:
    if not action.photo_id or not action.project_id:
        return False

    selected = action.payload.get("selected", False)
    image = data_manager.update_project_image(action.project_id, action.photo_id, {"is_selected": selected})
    return image is not None


def _process_favorite_action(action: BatchAction, data_manager: DataManager) -> bool:
    if not action.photo_id or not action.project_id:
        return False

    favorite = action.payload.get("favorite", False)
    image = data_manager.update_project_image(action.project_id, action.photo_id, {"is_favorite": favorite})
    return image is not None


def _process_comment_action(
    action: BatchAction,
    current_user: User,
    data_manager: DataManager,
) -> bool:
    if not action.photo_id or not action.project_id:
        return False

    comment_text = action.payload.get("commentText", "")
    parent_id = action.payload.get("parentId")

    if not comment_text.strip():
        return False

    timestamp = datetime.now()
    comment = Comment(
        id=str(uuid.uuid4()),
        image_id=action.photo_id,
        project_id=action.project_id,
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role,
        content=comment_text,
        parent_id=parent_id,
        created_at=timestamp,
        updated_at=timestamp,
    )

    created_comment = data_manager.create_comment(comment)
    return created_comment is not None


def _process_approve_action(action: BatchAction, data_manager: DataManager) -> bool:
    if not action.photo_id or not action.project_id:
        return False

    approved = action.payload.get("approved", False)

    project = data_manager.get_project_by_id(action.project_id)
    if not project:
        return False

    image = next((img for img in project.images if img.id == action.photo_id), None)
    if not image:
        return False

    current_tags = list(image.tags or [])

    if approved and "approved" not in current_tags:
        current_tags.append("approved")
    elif not approved and "approved" in current_tags:
        current_tags.remove("approved")

    updated_image = data_manager.update_project_image(action.project_id, action.photo_id, {"tags": current_tags})
    return updated_image is not None


def _process_download_action(action: BatchAction, current_user: User) -> bool:
    print(f"📥 Download logged for image {action.photo_id} by user {current_user.id}")
    return True
