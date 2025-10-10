"""File upload endpoints including bulk and chunked flows."""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api import deps
from app.core.dependencies import get_current_user, get_data_manager
from app.schemas import (
    ImageMetadata,
    ImageVersion,
    Project,
    ProjectImage,
    User,
    UserRole,
)
from app.services.data_manager import DataManager


router = APIRouter(tags=["Uploads"])


@router.post("/api/projects/{project_id}/upload")
async def upload_images(
    project: Project = Depends(deps.get_project),
    files: List[UploadFile] = File(...),
    category_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    data_manager: DataManager = Depends(get_data_manager),
):
    if current_user.role != UserRole.STUDIO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only studio users can upload images")

    if not category_id and project.categories:
        category_id = project.categories[0].id

    uploaded_images: List[ProjectImage] = []

    for file in files:
        if not file.content_type.startswith("image/"):
            continue

        image_id = str(uuid.uuid4())
        version = ImageVersion(
            id=f"ver-{image_id}",
            version="original",
            url=f"https://picsum.photos/800/600?random={len(project.images) + 1}",
            thumbnail=f"https://picsum.photos/300/200?random={len(project.images) + 1}",
            file_name=file.filename,
            uploaded_at=datetime.now(),
            is_latest=True,
            file_size=1024 * 1024,
        )

        image = ProjectImage(
            id=image_id,
            original_file_name=file.filename,
            category_id=category_id,
            versions=[version],
            metadata=ImageMetadata(
                width=3840,
                height=2560,
                camera="Uploaded Camera",
                lens="Uploaded Lens",
            ),
            tags=[],
            is_selected=False,
            is_favorite=False,
            comment_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        data_manager.add_image_to_project(project.id, image)
        uploaded_images.append(image)

    return {"message": f"Uploaded {len(uploaded_images)} images", "images": uploaded_images}


@router.post("/api/upload/chunk")
async def upload_chunk(
    chunk: UploadFile = File(...),
    chunkIndex: int = Form(...),
    chunkId: str = Form(...),
    fileId: str = Form(...),
    sessionId: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.STUDIO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only studio users can upload")

    try:
        chunk_data = await chunk.read()
        chunk_size = len(chunk_data)

        import hashlib

        etag = hashlib.md5(chunk_data).hexdigest()

        print(f"📦 Received chunk {chunkIndex} for file {fileId} (size: {chunk_size} bytes)")

        return {
            "chunkId": chunkId,
            "chunkIndex": chunkIndex,
            "size": chunk_size,
            "etag": etag,
            "status": "uploaded",
        }
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Chunk upload failed: {exc}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Chunk upload failed: {exc}")


@router.post("/api/upload/finalize")
async def finalize_upload(
    request: Dict,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.STUDIO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only studio users can upload")

    try:
        file_id = request.get("fileId")
        file_name = request.get("fileName")
        total_size = request.get("totalSize")
        chunks = request.get("chunks", [])

        if not all([file_id, file_name, total_size, chunks]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required fields")

        final_url = f"https://picsum.photos/800/600?random={file_id}"
        thumbnail_url = f"https://picsum.photos/300/200?random={file_id}"

        print(f"✅ Finalized upload for {file_name} ({total_size} bytes, {len(chunks)} chunks)")

        return {
            "fileId": file_id,
            "url": final_url,
            "thumbnail": thumbnail_url,
            "size": total_size,
            "status": "completed",
        }
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Upload finalization failed: {exc}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload finalization failed: {exc}")


@router.post("/api/upload/session")
async def create_upload_session(
    request: Dict,
    current_user: User = Depends(get_current_user),
    data_manager: DataManager = Depends(get_data_manager),
):
    if current_user.role != UserRole.STUDIO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only studio users can create upload sessions")

    try:
        project_id = request.get("projectId")
        project_name = request.get("projectName")
        settings = request.get("settings", {})

        if not project_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project ID is required")

        project = data_manager.get_project_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        session_id = str(uuid.uuid4())

        session_data = {
            "sessionId": session_id,
            "projectId": project_id,
            "projectName": project_name or project.name,
            "userId": current_user.id,
            "settings": {
                "chunkSize": settings.get("chunkSize", 5 * 1024 * 1024),
                "maxRetries": settings.get("maxRetries", 3),
                "parallelUploads": settings.get("parallelUploads", 3),
                "conflictResolution": settings.get("conflictResolution", "ask"),
                **settings,
            },
            "status": "pending",
            "createdAt": datetime.now().isoformat(),
            "totalFiles": 0,
            "totalBytes": 0,
            "uploadedBytes": 0,
        }

        print(f"🎯 Created upload session {session_id} for project {project.name}")
        return session_data
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Session creation failed: {exc}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Session creation failed: {exc}")


@router.get("/api/upload/session/{session_id}")
async def get_upload_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.STUDIO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return {
        "sessionId": session_id,
        "status": "uploading",
        "totalFiles": 150,
        "completedFiles": 75,
        "failedFiles": 2,
        "totalBytes": 500 * 1024 * 1024,
        "uploadedBytes": 250 * 1024 * 1024,
        "progress": 50.0,
        "estimatedTimeRemaining": 300,
        "updatedAt": datetime.now().isoformat(),
    }


@router.post("/api/upload/session/{session_id}/pause")
async def pause_upload_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.STUDIO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    print(f"⏸️ Paused upload session {session_id}")
    return {"sessionId": session_id, "status": "paused"}


@router.post("/api/upload/session/{session_id}/resume")
async def resume_upload_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.STUDIO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    print(f"▶️ Resumed upload session {session_id}")
    return {"sessionId": session_id, "status": "uploading"}


@router.post("/api/upload/session/{session_id}/cancel")
async def cancel_upload_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.STUDIO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    print(f"❌ Cancelled upload session {session_id}")
    return {"sessionId": session_id, "status": "cancelled"}


@router.post("/api/upload/bulk")
async def bulk_upload_with_categories(
    project_id: str = Form(...),
    folder_mappings: str = Form(...),
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    data_manager: DataManager = Depends(get_data_manager),
):
    if current_user.role != UserRole.STUDIO:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only studio users can upload")

    project = data_manager.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    try:
        mappings = json.loads(folder_mappings)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid folder mappings JSON") from exc

    uploaded_images: List[ProjectImage] = []
    folder_stats: Dict[str, Dict[str, int | str | None]] = {}

    for file in files:
        if not file.content_type.startswith("image/"):
            continue

        file_path = getattr(file, "path", file.filename)
        category_for_file = None

        for folder_path, category in mappings.items():
            if file_path.startswith(folder_path):
                category_for_file = category
                break

        if not category_for_file and project.categories:
            category_for_file = project.categories[0].id

        folder_name = file_path.split("/")[0] if "/" in file_path else "Root"
        if folder_name not in folder_stats:
            folder_stats[folder_name] = {"count": 0, "size": 0, "category": category_for_file}

        folder_stats[folder_name]["count"] += 1
        folder_stats[folder_name]["size"] += getattr(file, "size", 0) or 0

        image_id = str(uuid.uuid4())
        version = ImageVersion(
            id=f"ver-{image_id}",
            version="original",
            url=f"https://picsum.photos/800/600?random={len(uploaded_images) + 1}",
            thumbnail=f"https://picsum.photos/300/200?random={len(uploaded_images) + 1}",
            file_name=file.filename,
            uploaded_at=datetime.now(),
            is_latest=True,
            file_size=getattr(file, "size", 1024 * 1024) or 1024 * 1024,
        )

        image = ProjectImage(
            id=image_id,
            original_file_name=file.filename,
            category_id=category_for_file,
            versions=[version],
            metadata=ImageMetadata(
                width=3840,
                height=2560,
                camera="Bulk Upload Camera",
                lens="Bulk Upload Lens",
            ),
            tags=[],
            is_selected=False,
            is_favorite=False,
            comment_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        data_manager.add_image_to_project(project.id, image)
        uploaded_images.append(image)

    print(f"📤 Bulk uploaded {len(uploaded_images)} images across {len(folder_stats)} folders")

    return {
        "message": f"Successfully uploaded {len(uploaded_images)} images",
        "images": uploaded_images,
        "folderStats": folder_stats,
        "totalFolders": len(folder_stats),
    }
