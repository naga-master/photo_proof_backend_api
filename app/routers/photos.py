"""Photos router with CRUD operations."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.db.models import Photo, User, Project, UserPhotoFavorite, UserPhotoSelection
from app.schemas.photo import PhotoResponse, PhotoUpdate, PhotoListResponse
from app.api.deps import get_current_user


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
