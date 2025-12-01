"""Photos router with CRUD operations."""

import re
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.db.models import Photo, User, Project, UserPhotoFavorite, UserPhotoSelection
from app.db.models.photo import PhotoVersion
from app.db.models.project import Folder
from app.schemas.photo import PhotoResponse, PhotoUpdate, PhotoListResponse
from app.api.deps import get_current_user
from app.services.storage_service import get_storage_service
from app.services.version_service import VersionService
from app.middleware.package_restrictions import validate_photo_selection, update_usage_stats


router = APIRouter()


def origin_matches_pattern(origin: str, patterns: list[str]) -> bool:
    """Check if origin matches any of the allowed patterns (supports wildcards)."""
    for pattern in patterns:
        if pattern == origin:
            return True
        # Convert wildcard pattern to regex
        if '*' in pattern:
            regex_pattern = pattern.replace('.', r'\.').replace('*', r'[^:/]+')
            if re.match(f'^{regex_pattern}$', origin):
                return True
    return False


def resolve_user_id_for_selections(current_user, db, project=None) -> tuple[str | None, int | None]:
    """
    Resolve actual user_id for selection/favorite operations.
    Returns (user_id, client_id) tuple.
    
    - For clients: returns their linked user_id
    - For studio users viewing a project: returns the project's client's user_id
      (so studio can see what the client selected)
    - For clients without linked users: returns (None, client_id)
    """
    from app.db.models import Client
    
    # For clients, return their linked user_id
    if current_user.role == "client" or (isinstance(current_user.id, str) and current_user.id.startswith("client_")):
        try:
            client_id = int(current_user.id.replace("client_", ""))
            client = db.query(Client).filter(Client.id == client_id).first()
            if client and client.user_id:
                return (client.user_id, client_id)
            return (None, client_id)
        except (ValueError, AttributeError):
            return (None, None)
    
    # For studio users viewing a project, return the project's client's user_id
    # This allows studio to see what the client selected
    if project and current_user.studio_id == project.studio_id and project.client_id:
        client = db.query(Client).filter(Client.id == project.client_id).first()
        if client and client.user_id:
            return (client.user_id, client.id)
    
    return (current_user.id, None)


@router.get("/{photo_id}", response_model=PhotoResponse)
def get_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get a specific photo by ID.
    
    Requires authentication. Users can only access photos from:
    - Projects they own (studio owner/admin)
    - Projects they are clients on
    """
    photo = (
        db.query(Photo)
        .options(joinedload(Photo.project))
        .filter(Photo.id == photo_id)
        .first()
    )
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    # Check access permissions
    project = photo.project
    
    # Resolve user_id and client_id - pass project so studio sees client's selections
    actual_user_id, client_id = resolve_user_id_for_selections(current_user, db, project)
    
    has_access = False
    
    # Studio users can access all photos in their studio's projects
    if current_user.studio_id == project.studio_id:
        has_access = True
    
    # Clients can access photos from their projects
    if client_id and project.client_id == client_id:
        has_access = True
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this photo"
        )
    
    # Check if current user has selected/favorited this photo
    is_selected = False
    is_favorite = False
    if actual_user_id:
        is_selected = db.query(UserPhotoSelection).filter(
            UserPhotoSelection.user_id == actual_user_id,
            UserPhotoSelection.photo_id == photo_id
        ).first() is not None
        
        is_favorite = db.query(UserPhotoFavorite).filter(
            UserPhotoFavorite.user_id == actual_user_id,
            UserPhotoFavorite.photo_id == photo_id
        ).first() is not None
    
    # Return photo with user-specific flags
    return {
        **{c.name: getattr(photo, c.name) for c in photo.__table__.columns},
        "is_selected": is_selected,
        "is_favorite": is_favorite,
    }


@router.get("/projects/{project_id}/photos", response_model=PhotoListResponse)
def get_project_photos(
    project_id: int,
    folder_id: Optional[str] = Query(None, description="Filter by folder ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get all photos for a project with optional folder filtering.
    
    Returns photos ordered by order_index.
    """
    # Check project access
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Resolve user_id and client_id - pass project so studio sees client's selections
    actual_user_id, client_id = resolve_user_id_for_selections(current_user, db, project)
    
    # Verify access
    has_access = False
    if current_user.studio_id == project.studio_id:
        has_access = True
    if client_id and project.client_id == client_id:
        has_access = True
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this project"
        )
    
    # Build query
    query = db.query(Photo).filter(Photo.project_id == project_id)
    
    if folder_id:
        query = query.filter(Photo.folder_id == folder_id)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    photos = (
        query
        .order_by(Photo.order_index, Photo.created_at)
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # Get user's selections and favorites for these photos in batch
    photo_ids = [p.id for p in photos]
    user_selections = set()
    user_favorites = set()
    
    if actual_user_id and photo_ids:
        user_selections = set(
            s.photo_id for s in db.query(UserPhotoSelection.photo_id)
            .filter(
                UserPhotoSelection.user_id == actual_user_id,
                UserPhotoSelection.photo_id.in_(photo_ids)
            ).all()
        )
        
        user_favorites = set(
            f.photo_id for f in db.query(UserPhotoFavorite.photo_id)
            .filter(
                UserPhotoFavorite.user_id == actual_user_id,
                UserPhotoFavorite.photo_id.in_(photo_ids)
            ).all()
        )
    
    # Build response with user-specific flags
    photos_with_flags = []
    for photo in photos:
        photo_dict = {c.name: getattr(photo, c.name) for c in photo.__table__.columns}
        photo_dict["is_selected"] = photo.id in user_selections
        photo_dict["is_favorite"] = photo.id in user_favorites
        photos_with_flags.append(photo_dict)
    
    return {
        "photos": photos_with_flags,
        "total": total
    }


@router.get("/processing-issues")
def get_user_processing_issues(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get photos with processing issues for current user.
    
    Returns photos that failed variant generation or are still processing,
    limited to projects accessible by the current user.
    """
    # Get user's accessible projects
    if current_user.studio_id:
        # Studio user - can see all studio projects
        user_projects = db.query(Project).filter(
            Project.studio_id == current_user.studio_id
        ).all()
    elif current_user.client_profile:
        # Client user - can only see their own projects
        user_projects = db.query(Project).filter(
            Project.client_id == current_user.client_profile.id
        ).all()
    else:
        # No access
        user_projects = []
    
    project_ids = [p.id for p in user_projects]
    
    if not project_ids:
        return {
            "total_failed": 0,
            "photos": []
        }
    
    # Find photos with processing errors in user's projects
    failed_photos = (
        db.query(Photo)
        .filter(
            Photo.project_id.in_(project_ids),
            Photo.processing_error != None
        )
        .order_by(Photo.last_processing_attempt_at.desc())
        .limit(20)
        .all()
    )
    
    return {
        "total_failed": len(failed_photos),
        "photos": [
            {
                "id": p.id,
                "project_id": p.project_id,
                "filename": p.original_filename,
                "error": p.processing_error,
                "uploaded_at": p.created_at.isoformat() if p.created_at else None,
                "last_attempt": p.last_processing_attempt_at.isoformat() if p.last_processing_attempt_at else None,
                "attempts": p.processing_attempts,
            }
            for p in failed_photos
        ]
    }


@router.patch("/{photo_id}", response_model=PhotoResponse)
def update_photo(
    photo_id: int,
    photo_update: PhotoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Update a photo's metadata including selection and favorite status.
    
    - Studio users can update alt, order_index
    - Any authenticated user can update is_selected, is_favorite for themselves
    """
    photo = (
        db.query(Photo)
        .options(joinedload(Photo.project))
        .filter(Photo.id == photo_id)
        .first()
    )
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    # Resolve user_id and client_id
    actual_user_id, client_id = resolve_user_id_for_selections(current_user, db)
    
    project = photo.project
    update_data = photo_update.model_dump(exclude_unset=True)
    
    # Handle is_selected - update junction table for current user
    if 'is_selected' in update_data:
        is_selected = update_data.pop('is_selected')
        if actual_user_id:
            existing_selection = db.query(UserPhotoSelection).filter(
                UserPhotoSelection.user_id == actual_user_id,
                UserPhotoSelection.photo_id == photo_id
            ).first()
            
            if is_selected and not existing_selection:
                selection = UserPhotoSelection(user_id=actual_user_id, photo_id=photo_id)
                db.add(selection)
            elif not is_selected and existing_selection:
                db.delete(existing_selection)
    
    # Handle is_favorite - update junction table for current user
    if 'is_favorite' in update_data:
        is_favorite = update_data.pop('is_favorite')
        if actual_user_id:
            existing_favorite = db.query(UserPhotoFavorite).filter(
                UserPhotoFavorite.user_id == actual_user_id,
                UserPhotoFavorite.photo_id == photo_id
            ).first()
            
            if is_favorite and not existing_favorite:
                favorite = UserPhotoFavorite(user_id=actual_user_id, photo_id=photo_id)
                db.add(favorite)
            elif not is_favorite and existing_favorite:
                db.delete(existing_favorite)
    
    # For other fields (alt, order_index), only studio users can update
    if update_data:
        if current_user.studio_id != project.studio_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only studio users can update photo metadata"
            )
        for field, value in update_data.items():
            setattr(photo, field, value)
    
    db.commit()
    db.refresh(photo)
    
    # Get current user's selection/favorite status
    is_selected = False
    is_favorite = False
    if actual_user_id:
        is_selected = db.query(UserPhotoSelection).filter(
            UserPhotoSelection.user_id == actual_user_id,
            UserPhotoSelection.photo_id == photo_id
        ).first() is not None
        
        is_favorite = db.query(UserPhotoFavorite).filter(
            UserPhotoFavorite.user_id == actual_user_id,
            UserPhotoFavorite.photo_id == photo_id
        ).first() is not None
    
    return {
        **{c.name: getattr(photo, c.name) for c in photo.__table__.columns},
        "is_selected": is_selected,
        "is_favorite": is_favorite,
    }


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a photo.
    
    Only studio users can delete photos.
    Note: This doesn't delete the physical file, just the database record.
    """
    photo = (
        db.query(Photo)
        .options(joinedload(Photo.project))
        .filter(Photo.id == photo_id)
        .first()
    )
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    # Only studio users can delete
    if current_user.studio_id != photo.project.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can delete photos"
        )
    
    db.delete(photo)
    db.commit()





@router.get("/{photo_id}/favorites", response_model=List[str])
def get_photo_favorites(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[str]:
    """
    Get list of user IDs who favorited this photo.
    
    Only accessible by studio users.
    """
    photo = (
        db.query(Photo)
        .options(joinedload(Photo.project))
        .filter(Photo.id == photo_id)
        .first()
    )
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    # Only studio users can see favorites
    if current_user.studio_id != photo.project.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can view favorites"
        )
    
    favorites = (
        db.query(UserPhotoFavorite.user_id)
        .filter(UserPhotoFavorite.photo_id == photo_id)
        .all()
    )
    
    return [fav.user_id for fav in favorites]


@router.get("/{photo_id}/selections", response_model=List[str])
def get_photo_selections(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[str]:
    """
    Get list of user IDs who selected this photo.
    
    Only accessible by studio users.
    """
    photo = (
        db.query(Photo)
        .options(joinedload(Photo.project))
        .filter(Photo.id == photo_id)
        .first()
    )
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    # Only studio users can see selections
    if current_user.studio_id != photo.project.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can view selections"
        )
    
    selections = (
        db.query(UserPhotoSelection.user_id)
        .filter(UserPhotoSelection.photo_id == photo_id)
        .all()
    )
    
    return [sel.user_id for sel in selections]


# ===========================
# Photo Versions Endpoints
# ===========================

@router.get("/projects/{project_id}/photos/original")
def get_original_photos_for_matching(
    project_id: int,
    folder_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get all original photos in project for filename matching.
    Used by edited photo upload wizard.
    
    Returns photos with their current version filenames for matching against edited files.
    """
    # Verify project access
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check permissions (studio users only)
    if current_user.studio_id != project.studio_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Build query
    query = (
        db.query(Photo)
        .filter(Photo.project_id == project_id, Photo.status == "completed")
        .options(joinedload(Photo.folder))
    )
    
    # Apply filters
    if folder_id:
        query = query.filter(Photo.folder_id == folder_id)
    
    if search:
        query = query.filter(Photo.original_filename.ilike(f"%{search}%"))
    
    photos = query.order_by(Photo.order_index).all()
    
    # Get folders
    folders = db.query(Folder).filter(Folder.project_id == project_id).all()
    
    # Format response
    photos_data = []
    for photo in photos:
        photos_data.append({
            "id": photo.id,
            "original_filename": photo.original_filename,
            "src": photo.src,
            "thumbnail_path": photo.thumbnail_path,
            "folder_id": photo.folder_id,
            "folder_name": photo.folder.name if photo.folder else None,
            "current_version_filename": photo.original_filename,  # For now, use original filename
            "version_count": photo.version_count,
        })
    
    folders_data = [{"id": f.id, "name": f.name} for f in folders]
    
    return {
        "photos": photos_data,
        "folders": folders_data,
        "total": len(photos_data)
    }


@router.post("/photos/versions/match")
def match_edited_filenames(
    request: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Match edited filenames to existing photos using smart matching algorithm.
    
    Request body:
    {
        "project_id": int,
        "filenames": ["IMG_1234_edited.jpg", ...]
    }
    
    Returns matched and unmatched filenames with confidence scores.
    """
    project_id = request.get("project_id")
    filenames = request.get("filenames", [])
    
    if not project_id or not filenames:
        raise HTTPException(status_code=400, detail="project_id and filenames required")
    
    # Verify project access
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if current_user.studio_id != project.studio_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get all photos in project
    photos = db.query(Photo).filter(
        Photo.project_id == project_id,
        Photo.status == "completed"
    ).all()
    
    # Use version service to match filenames
    storage = get_storage_service()
    version_service = VersionService(db, storage)
    
    result = version_service.match_filenames(filenames, photos)
    
    return result


@router.post("/photos/versions/batch")
async def create_photo_versions_batch(
    request: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Create multiple photo versions in batch.
    Generates presigned URLs for uploading edited photos.
    
    Request body:
    {
        "mappings": [
            {
                "photo_id": int,
                "file_metadata": {
                    "filename": str,
                    "content_type": str,
                    "file_size": int
                },
                "version_label": Optional[str],
                "mapping_type": "auto" | "manual"
            }
        ]
    }
    
    Returns upload tokens similar to regular photo upload.
    """
    from app.services.upload_service import UploadService
    from app.core.config import get_settings
    
    settings = get_settings()
    mappings = request.get("mappings", [])
    
    if not mappings:
        raise HTTPException(status_code=400, detail="No mappings provided")
    
    # Validate file sizes
    for mapping in mappings:
        file_metadata = mapping.get("file_metadata", {})
        file_size_mb = file_metadata.get("file_size", 0) / (1024 * 1024)
        if file_size_mb > settings.max_upload_file_size_mb:
            raise HTTPException(
                status_code=400,
                detail=f"File {file_metadata.get('filename')} exceeds {settings.max_upload_file_size_mb}MB limit"
            )
    
    # Validate all photo IDs and check version limits
    photo_ids = [m.get("photo_id") for m in mappings]
    photos = db.query(Photo).filter(Photo.id.in_(photo_ids)).all()
    
    if len(photos) != len(photo_ids):
        raise HTTPException(status_code=404, detail="One or more photos not found")
    
    # Check permissions - all photos must belong to user's studio
    for photo in photos:
        project = db.query(Project).filter(Project.id == photo.project_id).first()
        if not project or current_user.studio_id != project.studio_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check version limit
        if photo.version_count >= settings.max_photo_versions:
            raise HTTPException(
                status_code=400,
                detail=f"Photo {photo.id} has reached maximum version limit ({settings.max_photo_versions})"
            )
    
    # Generate upload tokens using existing upload service
    # This will create tokens that can be used with the regular upload endpoint
    storage = get_storage_service()
    upload_service = UploadService(storage)
    
    # Create upload session
    first_photo = photos[0]
    project = db.query(Project).filter(Project.id == first_photo.project_id).first()
    
    tokens_and_urls = []
    for mapping in mappings:
        photo_id = mapping.get("photo_id")
        file_metadata = mapping.get("file_metadata", {})
        version_label = mapping.get("version_label")
        
        # Generate upload token for version upload
        upload_token, upload_url = upload_service.generate_upload_token(
            db=db,
            project_id=project.id,
            filename=file_metadata.get("filename"),
            content_type=file_metadata.get("content_type", "image/jpeg"),
            file_size=file_metadata.get("file_size", 0),
            user_id=current_user.id,
            folder_id=None,  # Versions don't change folder
        )
        
        # Set version upload fields on token
        upload_token.is_version_upload = True
        upload_token.target_photo_id = photo_id
        upload_token.version_label = version_label
        upload_token.mapping_type = mapping.get("mapping_type", "auto")
        
        db.add(upload_token)
        
        tokens_and_urls.append({
            "upload_url": upload_url,
            "token": upload_token.token,
            "photo_id": photo_id,
            "expires_at": upload_token.expires_at.isoformat()
        })
    
    db.commit()
    
    return {
        "tokens": tokens_and_urls,
        "total_files": len(tokens_and_urls)
    }


@router.get("/{photo_id}/variant/{quality}")
def get_photo_variant(
    photo_id: int,
    quality: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get specific quality variant of a photo.
    
    Quality levels: thumbnail, low, medium, high, print
    """
    from fastapi.responses import FileResponse
    from pathlib import Path
    from app.core.config import get_settings
    
    settings = get_settings()
    
    # Get photo
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    # Check access permissions
    project = db.query(Project).filter(Project.id == photo.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Studio users can access all photos in their studio's projects
    has_access = False
    if current_user.studio_id == project.studio_id:
        has_access = True
    # Clients can access photos from their projects
    elif current_user.client_profile and project.client_id == current_user.client_profile.id:
        has_access = True
    
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Try multiple path strategies to find the variant file
    file_path = None
    
    # Strategy 1: New nested structure - projects/{project_id}/variants/{photo_id}/{quality}.webp
    nested_path = Path("uploads") / f"projects/{project.id}/variants/{photo_id}/{quality}.webp"
    if nested_path.exists():
        file_path = nested_path
    
    # Strategy 2: Check variants_json from database
    if not file_path and photo.variants_json:
        import json
        try:
            variants = json.loads(photo.variants_json)
            variant_path = variants.get(quality)
            if variant_path:
                db_path = Path("uploads") / variant_path
                if db_path.exists():
                    file_path = db_path
        except (json.JSONDecodeError, AttributeError):
            pass
    
    # Strategy 3: Old flat structure - uploads/variants/{photo_id}_{quality}.webp
    if not file_path:
        flat_path = Path("uploads/variants") / f"{photo_id}_{quality}.webp"
        if flat_path.exists():
            file_path = flat_path
    
    # Strategy 4: Fallback to original photo
    if not file_path:
        original_path = Path("uploads") / photo.storage_path
        if original_path.exists():
            file_path = original_path
        else:
            raise HTTPException(status_code=404, detail="Image file not found")
    
    # Get origin from request for CORS
    origin = request.headers.get("origin", "")
    
    # Prepare CORS headers with wildcard pattern matching
    cors_headers = {}
    if origin and origin_matches_pattern(origin, settings.cors_origins):
        cors_headers["Access-Control-Allow-Origin"] = origin
        cors_headers["Access-Control-Allow-Credentials"] = "true"
        cors_headers["Access-Control-Allow-Methods"] = "*"
        cors_headers["Access-Control-Allow-Headers"] = "*"
    
    # Serve file with caching and CORS headers
    # Include version in ETag to force cache invalidation when CORS changes
    return FileResponse(
        file_path,
        media_type=photo.mime_type or "image/jpeg",
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "ETag": f'"{photo.id}-{quality}-v2"',  # v2 to invalidate old cache
            **cors_headers,  # Add CORS headers
        }
    )


@router.get("/photos/{photo_id}/versions")
def get_photo_versions(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get version history for a photo (studio users only).
    
    Returns all versions with current version highlighted.
    """
    # Get photo
    photo = db.query(Photo).options(joinedload(Photo.project)).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    # Check permissions (studio users only)
    if current_user.studio_id != photo.project.studio_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get version service
    storage = get_storage_service()
    version_service = VersionService(db, storage)
    
    # Get all versions
    versions = version_service.get_version_history(photo_id)
    
    # Format response
    versions_data = []
    for version in versions:
        versions_data.append({
            "id": version.id,
            "version_number": version.version_number,
            "filename": version.original_filename,
            "src": version.src,
            "thumbnail_path": version.thumbnail_path,
            "version_label": version.version_label,
            "is_original": version.is_original,
            "is_current": version.id == photo.current_version_id,
            "uploaded_by": version.uploaded_by,
            "uploaded_at": version.created_at.isoformat(),
            "file_size": version.file_size,
            "width": version.width,
            "height": version.height,
        })
    
    # Get current version
    current_version_data = None
    if photo.current_version_id:
        for v in versions_data:
            if v["id"] == photo.current_version_id:
                current_version_data = v
                break
    
    return {
        "photo_id": photo_id,
        "current_version": current_version_data,
        "versions": versions_data,
        "total_versions": len(versions_data)
    }


@router.patch("/photos/{photo_id}/versions/{version_id}/activate")
def set_active_version(
    photo_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Set a different version as the current active version (revert to older version).
    Studio users only.
    """
    # Get photo
    photo = db.query(Photo).options(joinedload(Photo.project)).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    # Check permissions
    if current_user.studio_id != photo.project.studio_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Use version service to set active version
    storage = get_storage_service()
    version_service = VersionService(db, storage)
    
    try:
        updated_photo = version_service.set_current_version(photo_id, version_id)
        return {
            "photo_id": photo_id,
            "current_version_id": updated_photo.current_version_id,
            "message": "Version activated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
