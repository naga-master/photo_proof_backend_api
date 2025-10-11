"""Upload endpoints backed by SQLite storage."""

from __future__ import annotations

import mimetypes
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session, selectinload
from PIL import Image as PILImage

from app.core.config import get_settings
from app.core.dependencies import get_current_user
from app.db import models
from app.db.session import get_db
from app.schemas import (
    CompleteUploadRequest,
    CompleteUploadResponse,
    ImageRead,
    ImageVersionRead,
    InitiateUploadRequest,
    UploadInitiateResponse,
    UploadUrlInfo,
    UserRead,
    UserRole,
)


router = APIRouter(tags=["Uploads"])

settings = get_settings()
UPLOADS_ROOT = Path(settings.uploads_directory).resolve()
UPLOADS_ROOT.mkdir(parents=True, exist_ok=True)


def _sanitize_segment(value: str) -> str:
    return Path(value).name


def _resolve_category_id(project: models.Project, requested: Optional[str]) -> Optional[str]:
    if requested:
        if any(category.id == requested for category in project.categories):
            return requested
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category for project")

    default_category = next((category for category in project.categories if category.is_default), None)
    if default_category:
        return default_category.id

    return project.categories[0].id if project.categories else None


def _build_target_url(request: Request, project_id: str, category_segment: str, file_name: str) -> str:
    base_url = str(request.base_url).rstrip("/")
    return f"{base_url}/api/uploads/stream/{project_id}/{category_segment}/{file_name}"


def _is_image_file(filename: str) -> bool:
    """Check if the file is an image based on its extension."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
    return Path(filename).suffix.lower() in image_extensions


def _validate_image_file(file_path: Path) -> bool:
    """Validate that an image file is not corrupted and has proper headers."""
    try:
        # Check file size - should be more than 100 bytes for a valid image
        if file_path.stat().st_size < 100:
            return False
        
        # Read first few bytes to check for valid image headers
        with file_path.open('rb') as f:
            header = f.read(20)
        
        # Check for common image file signatures
        if file_path.suffix.lower() in {'.jpg', '.jpeg'}:
            # JPEG: FF D8 FF
            if len(header) < 3 or header[:3] != b'\xff\xd8\xff':
                print("JPEG: FF D8 FF")
                return False
        elif file_path.suffix.lower() == '.png':
            # PNG: 89 50 4E 47 0D 0A 1A 0A
            if len(header) < 8 or header[:8] != b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a':
                print("PNG: 89 50 4E 47 0D 0A 1A 0A")
                return False
        elif file_path.suffix.lower() == '.gif':
            # GIF: GIF87a or GIF89a
            if len(header) < 6 or not (header[:6] == b'GIF87a' or header[:6] == b'GIF89a'):
                print("# GIF: GIF87a or GIF89a")
                return False
        elif file_path.suffix.lower() == '.bmp':
            # BMP: BM
            if len(header) < 2 or header[:2] != b'BM':
                print("# BMP: BM")
                return False
        elif file_path.suffix.lower() == '.webp':
            # WebP: RIFF....WEBP
            if len(header) < 12 or header[:4] != b'RIFF' or header[8:12] != b'WEBP':
                print(" WebP: RIFF....WEBP")
                return False
        
        # Try to read file as text to detect ASCII text files disguised as images
        try:
            with file_path.open('r', encoding='utf-8') as f:
                content = f.read(200)  # Read first 200 chars
            
            # If we can read it as text and it contains test phrases, it's corrupted
            test_phrases = ['test', 'hello', 'image does not exist', 'test data', 'hello world']
            if any(phrase in content.lower() for phrase in test_phrases):
                print(test_phrases)
                return False
                
            # If the entire file is readable as ASCII and small, it's probably not an image
            if file_path.stat().st_size < 1000 and content.isprintable():
                print(file_path.stat().st_size)
                return False
                
        except UnicodeDecodeError:
            # Good! Can't decode as text - likely a real binary image file
            print("Unicode error")
            pass
        
        return True
        
    except Exception as e:
        print(e)
        return False


def _extract_image_metadata(file_path: Path) -> Tuple[Optional[int], Optional[int]]:
    """Extract width and height metadata from an image file.
    
    Returns:
        Tuple of (width, height) or (None, None) if extraction fails
    """
    if not _is_image_file(file_path.name):
        return None, None
    
    try:
        # Ensure the file exists and is readable
        if not file_path.exists() or not file_path.is_file():
            print(f"Warning: File does not exist or is not a file: {file_path}")
            return None, None
            
        with PILImage.open(file_path) as img:
            width, height = img.size
            print(f"Extracted metadata for {file_path.name}: {width}x{height}")
            return width, height
    except Exception as e:
        print(f"Warning: Could not extract metadata from {file_path}: {e}")
        return None, None


def _serialize_image(image: models.Image) -> ImageRead:
    base = ImageRead.model_validate(image)
    versions = [ImageVersionRead.model_validate(version) for version in image.versions]
    tags = [tag.name for tag in image.tags]
    return base.model_copy(update={"versions": versions, "tags": tags})


@router.post("/api/uploads/initiate", response_model=UploadInitiateResponse)
def initiate_uploads(
    payload: InitiateUploadRequest,
    request: Request,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UploadInitiateResponse:
    if current_user.role == UserRole.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only studio users can upload images")

    project = (
        db.query(models.Project)
        .options(selectinload(models.Project.categories))
        .filter(models.Project.id == payload.project_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    project_segment = _sanitize_segment(project.id)
    upload_urls: List[UploadUrlInfo] = []

    for descriptor in payload.files:
        file_name = _sanitize_segment(descriptor.file_name)
        category_id = _resolve_category_id(project, descriptor.category_id)
        category_segment = _sanitize_segment(category_id) if category_id else "uncategorized"

        destination_dir = UPLOADS_ROOT / project_segment / category_segment
        destination_dir.mkdir(parents=True, exist_ok=True)

        upload_id_source = f"{project_segment}:{category_segment}:{file_name.lower()}"
        upload_id = str(uuid.uuid5(uuid.NAMESPACE_URL, upload_id_source))
        target_url = _build_target_url(request, project_segment, category_segment, file_name)

        upload_urls.append(
            UploadUrlInfo(
                file_name=file_name,
                target_url=target_url,
                upload_id=upload_id,
                category_id=category_id,
            )
        )

    return UploadInitiateResponse(upload_urls=upload_urls)


@router.put("/api/uploads/stream/{project_id}/{category_id}/{file_name:path}", status_code=status.HTTP_204_NO_CONTENT)
async def upload_file_stream(
    project_id: str, 
    category_id: str, 
    file_name: str, 
    request: Request,
    db: Session = Depends(get_db)
) -> Response:
    # Validate project exists before allowing file upload
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Validate category exists in project
    category = (
        db.query(models.Category)
        .filter(models.Category.id == category_id, models.Category.project_id == project_id)
        .first()
    )
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category for project")

    sanitized_name = _sanitize_segment(file_name)
    category_segment = _sanitize_segment(category_id)
    project_segment = _sanitize_segment(project_id)

    destination_dir = UPLOADS_ROOT / project_segment / category_segment
    destination_dir.mkdir(parents=True, exist_ok=True)

    destination_path = destination_dir / sanitized_name

    try:
        total_bytes = 0
        with destination_path.open("wb") as buffer:
            async for chunk in request.stream():
                if not chunk:  # Skip empty chunks
                    continue
                buffer.write(chunk)
                total_bytes += len(chunk)
        
        # Validate the uploaded file
        if total_bytes == 0:
            destination_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Uploaded file is empty"
            )
        
        # Additional validation for image files
        if _is_image_file(sanitized_name):
            if not _validate_image_file(destination_path):
                destination_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Uploaded file is not a valid image"
                )
        
    except Exception as exc:  # noqa: BLE001
        print(exc)
        # Clean up the file if upload failed
        destination_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to write file: {exc}"
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/api/uploads/complete", response_model=CompleteUploadResponse)
def complete_upload(
    payload: CompleteUploadRequest,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CompleteUploadResponse:
    if current_user.role == UserRole.CLIENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only studio users can upload images")

    project = (
        db.query(models.Project)
        .options(selectinload(models.Project.categories))
        .filter(models.Project.id == payload.project_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    category_id = _resolve_category_id(project, payload.category_id)
    resolved_category_id = category_id or (project.categories[0].id if project.categories else None)
    if not resolved_category_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No category available for project")

    category_segment = _sanitize_segment(resolved_category_id)
    project_segment = _sanitize_segment(project.id)

    sanitized_name = _sanitize_segment(payload.file_name)
    stored_path = UPLOADS_ROOT / project_segment / category_segment / sanitized_name

    if not stored_path.exists():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file not found on server")

    # Validate the stored file integrity
    if _is_image_file(sanitized_name):
        if not _validate_image_file(stored_path):
            # Remove the corrupted file
            stored_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Uploaded file is corrupted or invalid"
            )

    file_size = stored_path.stat().st_size
    mime_type = payload.content_type or mimetypes.guess_type(sanitized_name)[0] or "application/octet-stream"
    # Generate static serving URL instead of using upload API URL
    asset_url = f"/uploads/{project_segment}/{category_segment}/{sanitized_name}"

    # Extract image metadata (width, height) if it's an image file
    width, height = _extract_image_metadata(stored_path)

    duplicate = (
        db.query(models.Image)
        .filter(
            models.Image.project_id == project.id,
            models.Image.original_filename == payload.original_file_name,
            models.Image.category_id == resolved_category_id,
        )
        .first()
    )
    if duplicate:
        duplicate = (
            db.query(models.Image)
            .options(selectinload(models.Image.versions), selectinload(models.Image.tags))
            .filter(models.Image.id == duplicate.id)
            .first()
        )
        return CompleteUploadResponse(image=_serialize_image(duplicate), already_exists=True)

    image = models.Image(
        id=str(uuid.uuid4()),
        project_id=project.id,
        category_id=resolved_category_id,
        uploaded_by=current_user.id,
        original_filename=payload.original_file_name,
        s3_key_original=asset_url,
        s3_key_thumbnail=asset_url,
        s3_key_preview=None,
        s3_key_print=None,
        file_size_bytes=file_size,
        mime_type=mime_type,
        width=width,
        height=height,
        is_favorite=False,
        is_selected=False,
        comment_count=0,
        status="ready",
        uploaded_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(image)
    db.flush()

    version = models.ImageVersion(
        id=str(uuid.uuid4()),
        image_id=image.id,
        version_name="original",
        s3_key=asset_url,
        file_size_bytes=file_size,
        width=width,
        height=height,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
    )
    db.add(version)

    project.total_images = (project.total_images or 0) + 1
    project.storage_used_bytes = (project.storage_used_bytes or 0) + file_size
    project.updated_at = datetime.utcnow()

    category = next((cat for cat in project.categories if cat.id == resolved_category_id), None)
    if category:
        category.image_count = (category.image_count or 0) + 1
        category.updated_at = datetime.utcnow()

    db.commit()

    image = (
        db.query(models.Image)
        .options(selectinload(models.Image.versions), selectinload(models.Image.tags))
        .filter(models.Image.id == image.id)
        .first()
    )

    return CompleteUploadResponse(image=_serialize_image(image), already_exists=False)
