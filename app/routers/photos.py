"""Photos router with CRUD operations."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.db.models import Photo, User, Project, UserPhotoFavorite, UserPhotoSelection
from app.db.models.photo import PhotoVersion
from app.db.models.project import Folder
from app.schemas.photo import PhotoResponse, PhotoUpdate, PhotoListResponse
from app.api.deps import get_current_user
from app.services.storage_service import get_storage_service
from app.services.version_service import VersionService


router = APIRouter()


@router.get("/{photo_id}", response_model=PhotoResponse)
def get_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Photo:
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
    
    # Studio users can access all photos in their studio's projects
    if current_user.studio_id == project.studio_id:
        return photo
    
    # Clients can access photos from their projects
    if current_user.client_profile and project.client_id == current_user.client_profile.id:
        return photo
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to access this photo"
    )


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
    
    # Verify access
    if current_user.studio_id != project.studio_id:
        if not (current_user.client_profile and project.client_id == current_user.client_profile.id):
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
    
    return {
        "photos": photos,
        "total": total
    }


@router.patch("/{photo_id}", response_model=PhotoResponse)
def update_photo(
    photo_id: int,
    photo_update: PhotoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Photo:
    """
    Update a photo's metadata.
    
    Only studio users can update photos.
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
    
    # Only studio users can update
    if current_user.studio_id != photo.project.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can update photos"
        )
    
    # Update fields
    update_data = photo_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(photo, field, value)
    
    db.commit()
    db.refresh(photo)
    
    return photo


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


@router.post("/{photo_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
def favorite_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Mark a photo as favorite for the current user.
    
    Clients and studio users can favorite photos.
    """
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    # Check if already favorited
    existing = (
        db.query(UserPhotoFavorite)
        .filter(
            UserPhotoFavorite.user_id == current_user.id,
            UserPhotoFavorite.photo_id == photo_id
        )
        .first()
    )
    
    if not existing:
        favorite = UserPhotoFavorite(
            user_id=current_user.id,
            photo_id=photo_id
        )
        db.add(favorite)
        db.commit()


@router.delete("/{photo_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
def unfavorite_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Remove favorite mark from a photo for the current user.
    """
    favorite = (
        db.query(UserPhotoFavorite)
        .filter(
            UserPhotoFavorite.user_id == current_user.id,
            UserPhotoFavorite.photo_id == photo_id
        )
        .first()
    )
    
    if favorite:
        db.delete(favorite)
        db.commit()


@router.post("/{photo_id}/select", status_code=status.HTTP_204_NO_CONTENT)
def select_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Mark a photo as selected for the current user.
    
    Used by clients to select photos they want to purchase.
    """
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    # Check if already selected
    existing = (
        db.query(UserPhotoSelection)
        .filter(
            UserPhotoSelection.user_id == current_user.id,
            UserPhotoSelection.photo_id == photo_id
        )
        .first()
    )
    
    if not existing:
        selection = UserPhotoSelection(
            user_id=current_user.id,
            photo_id=photo_id
        )
        db.add(selection)
        db.commit()


@router.delete("/{photo_id}/select", status_code=status.HTTP_204_NO_CONTENT)
def unselect_photo(
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Remove selection mark from a photo for the current user.
    """
    selection = (
        db.query(UserPhotoSelection)
        .filter(
            UserPhotoSelection.user_id == current_user.id,
            UserPhotoSelection.photo_id == photo_id
        )
        .first()
    )
    
    if selection:
        db.delete(selection)
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
        
        # Store version metadata in upload token for later processing
        # We'll modify upload completion to handle version creation
        upload_token, upload_url = upload_service.generate_upload_token(
            db=db,
            project_id=project.id,
            filename=file_metadata.get("filename"),
            content_type=file_metadata.get("content_type", "image/jpeg"),
            file_size=file_metadata.get("file_size", 0),
            user_id=current_user.id,
            folder_id=None,  # Versions don't change folder
        )
        
        # Store version metadata in a custom field (we'll need to add this to UploadToken model)
        # For now, store in session metadata
        upload_token.version_metadata = {
            "is_version": True,
            "target_photo_id": photo_id,
            "version_label": version_label,
            "mapping_type": mapping.get("mapping_type", "auto")
        }
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
