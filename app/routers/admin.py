"""Admin router for system management and recovery operations."""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user
from app.db.models import Photo, User
from app.services.upload_service import _process_photo_variants_background


router = APIRouter(prefix="/admin", tags=["Admin"])


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require admin/studio owner access."""
    if current_user.role not in ['studio_owner', 'studio_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.post("/photos/{photo_id}/reprocess")
async def reprocess_photo(
    photo_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Manually trigger variant generation for a photo.
    
    Useful for retrying failed processing or regenerating variants
    after system improvements.
    """
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    # Verify studio access
    if current_user.studio_id != photo.project.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this photo"
        )
    
    # Reset error state
    photo.processing_error = None
    photo.processing_attempts = 0
    photo.status = 'processing'
    db.commit()
    
    # Trigger background processing
    background_tasks.add_task(
        _process_photo_variants_background,
        photo_id=photo.id,
        storage_path=photo.storage_path,
        project_id=photo.project_id
    )
    
    return {
        "message": f"Reprocessing photo {photo_id}",
        "photo_id": photo_id,
        "status": "processing"
    }


@router.post("/photos/reprocess-failed")
async def reprocess_failed_photos(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    limit: int = 50
):
    """
    Reprocess all photos with processing errors.
    
    Batch operation to retry all failed photos, limited to prevent
    overwhelming the system.
    """
    # Find photos without variants or with errors in this studio
    query = db.query(Photo).join(Photo.project)
    
    if current_user.studio_id:
        from app.db.models.project import Project
        query = query.filter(Project.studio_id == current_user.studio_id)
    
    failed_photos = (
        query
        .filter(
            (Photo.variants_json == None) | (Photo.processing_error != None)
        )
        .limit(limit)
        .all()
    )
    
    count = 0
    for photo in failed_photos:
        photo.processing_error = None
        photo.processing_attempts = 0
        photo.status = 'processing'
        
        background_tasks.add_task(
            _process_photo_variants_background,
            photo_id=photo.id,
            storage_path=photo.storage_path,
            project_id=photo.project_id
        )
        count += 1
    
    db.commit()
    
    return {
        "message": f"Reprocessing {count} photos",
        "count": count,
        "status": "processing"
    }


@router.get("/photos/processing-status")
def get_processing_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Get overview of photo processing status for this studio.
    
    Returns counts and recent failures to help monitor system health.
    """
    # Build query for studio's photos
    query = db.query(Photo).join(Photo.project)
    
    if current_user.studio_id:
        from app.db.models.project import Project
        query = query.filter(Project.studio_id == current_user.studio_id)
    
    # Count statistics
    total_photos = query.count()
    
    processing = query.filter(Photo.status == 'processing').count()
    
    completed = query.filter(
        Photo.status == 'completed',
        Photo.variants_json != None,
        Photo.processing_error == None
    ).count()
    
    failed = query.filter(Photo.processing_error != None).count()
    
    no_variants = query.filter(
        Photo.status == 'completed',
        Photo.variants_json == None
    ).count()
    
    # Get recent failures
    recent_failures = (
        query
        .filter(Photo.processing_error != None)
        .order_by(Photo.last_processing_attempt_at.desc())
        .limit(20)
        .all()
    )
    
    return {
        "total_photos": total_photos,
        "processing": processing,
        "completed_with_variants": completed,
        "failed": failed,
        "missing_variants": no_variants,
        "recent_failures": [
            {
                "id": p.id,
                "filename": p.original_filename,
                "error": p.processing_error,
                "attempts": p.processing_attempts,
                "last_attempt": p.last_processing_attempt_at.isoformat() if p.last_processing_attempt_at else None,
                "project_id": p.project_id,
            }
            for p in recent_failures
        ]
    }
