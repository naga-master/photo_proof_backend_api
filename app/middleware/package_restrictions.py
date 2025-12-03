"""Package restriction enforcement middleware."""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import Project, ServicePackage, Photo, UserPhotoSelection


class PackageRestrictionError(HTTPException):
    """Custom exception for package restriction violations."""
    
    def __init__(self, detail: str, restriction_type: str = "general"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "PackageRestrictionViolation",
                "message": detail,
                "restriction_type": restriction_type,
            }
        )


def get_package_restrictions(project_id: int, db: Session) -> Optional[Dict[str, Any]]:
    """
    Get package restrictions for a project.
    Uses package_snapshot if available, otherwise falls back to current package.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None
    
    # Try to use package snapshot first (frozen at project creation)
    if project.package_snapshot:
        snapshot = json.loads(project.package_snapshot) if isinstance(project.package_snapshot, str) else project.package_snapshot
        return snapshot.get('restrictions')
    
    # Fall back to current package restrictions
    if project.package_id:
        package = db.query(ServicePackage).filter(ServicePackage.id == project.package_id).first()
        if package and package.restrictions:
            return json.loads(package.restrictions) if isinstance(package.restrictions, str) else package.restrictions
    
    return None


def get_project_usage_stats(project_id: int, db: Session) -> Dict[str, Any]:
    """
    Get current usage statistics for a project.
    Returns dict with photos_selected, video_gb_used, etc.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return {"photos_selected": 0, "video_gb_used": 0}
    
    if project.usage_stats:
        stats = json.loads(project.usage_stats) if isinstance(project.usage_stats, str) else project.usage_stats
        return stats
    
    return {"photos_selected": 0, "video_gb_used": 0}


def update_usage_stats(project_id: int, db: Session, **updates) -> None:
    """
    Update usage statistics for a project.
    Example: update_usage_stats(project_id, db, photos_selected=10)
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return
    
    current_stats = get_project_usage_stats(project_id, db)
    current_stats.update(updates)
    
    project.usage_stats = json.dumps(current_stats)
    db.commit()


def validate_photo_selection(user_id: str, project_id: int, photo_id: int, db: Session) -> bool:
    """
    Validate if user can select another photo based on package restrictions.
    
    Raises:
        PackageRestrictionError: If selection limit is reached
    
    Returns:
        True if selection is allowed
    """
    restrictions = get_package_restrictions(project_id, db)
    
    # No restrictions = no limits
    if not restrictions or 'photo_selection_limit' not in restrictions:
        return True
    
    limit = restrictions['photo_selection_limit']
    
    # Count current selections for this user in this project
    current_count = db.query(UserPhotoSelection).join(Photo).filter(
        Photo.project_id == project_id,
        UserPhotoSelection.user_id == user_id
    ).count()
    
    # Check if adding one more would exceed limit
    if current_count >= limit:
        raise PackageRestrictionError(
            f"Photo selection limit reached. You can select up to {limit} photos for this project.",
            restriction_type="photo_selection_limit"
        )
    
    return True


def validate_video_upload(project_id: int, video_size_gb: float, db: Session) -> bool:
    """
    Validate if video upload is allowed based on package restrictions.
    
    Raises:
        PackageRestrictionError: If video not supported or size exceeds limit
    
    Returns:
        True if upload is allowed
    """
    restrictions = get_package_restrictions(project_id, db)
    
    # No restrictions = no limits
    if not restrictions:
        return True
    
    # Check if video support is enabled
    if not restrictions.get('video_support_enabled', False):
        raise PackageRestrictionError(
            "Video uploads are not supported in this package.",
            restriction_type="video_not_supported"
        )
    
    # Check video size limit
    if 'video_max_gb' in restrictions:
        max_gb = restrictions['video_max_gb']
        usage_stats = get_project_usage_stats(project_id, db)
        current_gb = usage_stats.get('video_gb_used', 0)
        
        if current_gb + video_size_gb > max_gb:
            raise PackageRestrictionError(
                f"Video storage limit exceeded. Limit: {max_gb}GB, Current: {current_gb}GB, Trying to add: {video_size_gb}GB",
                restriction_type="video_size_limit"
            )
    
    return True


def check_editing_period(project_id: int, db: Session) -> bool:
    """
    Check if editing is still allowed based on editing period restriction.
    
    Raises:
        PackageRestrictionError: If editing period has expired
    
    Returns:
        True if editing is still allowed
    """
    restrictions = get_package_restrictions(project_id, db)
    
    # No restrictions = no limits
    if not restrictions or 'editing_period_months' not in restrictions:
        return True
    
    editing_months = restrictions['editing_period_months']
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return True
    
    # Use first photo upload date as start date
    first_photo = db.query(Photo).filter(
        Photo.project_id == project_id
    ).order_by(Photo.created_at).first()
    
    if not first_photo:
        return True  # No photos yet, allow editing
    
    deadline = first_photo.created_at + relativedelta(months=editing_months)
    
    if datetime.now() > deadline:
        raise PackageRestrictionError(
            f"Editing period has expired. Editing was allowed for {editing_months} months from first upload.",
            restriction_type="editing_period_expired"
        )
    
    return True


def check_whatsapp_integration_enabled(project_id: int, db: Session) -> bool:
    """
    Check if WhatsApp integration is enabled for this package.
    
    Returns:
        True if WhatsApp is enabled, False otherwise
    """
    restrictions = get_package_restrictions(project_id, db)
    
    if not restrictions:
        return False
    
    return restrictions.get('whatsapp_integration', False)


def calculate_archival_date(project_id: int, db: Session) -> Optional[datetime]:
    """
    Calculate when the project should be archived based on package restrictions.
    
    Returns:
        datetime of archival date, or None if archival not configured
    """
    restrictions = get_package_restrictions(project_id, db)
    
    if not restrictions:
        return None
    
    archival_config = restrictions.get('archival')
    if not archival_config or not archival_config.get('enabled'):
        return None
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None
    
    years = archival_config.get('archive_after', {}).get('years', 0)
    months = archival_config.get('archive_after', {}).get('months', 0)
    
    # Calculate from project creation date
    archival_date = project.created_at + relativedelta(years=years, months=months)
    
    return archival_date


def calculate_retention_deadline(project_id: int, db: Session) -> Optional[datetime]:
    """
    Calculate when the project should be deleted based on retention period.
    
    Returns:
        datetime of deletion deadline, or None if retention not configured
    """
    restrictions = get_package_restrictions(project_id, db)
    
    if not restrictions:
        return None
    
    retention_years = restrictions.get('retention_years')
    retention_months = restrictions.get('retention_months', 0)
    
    if not retention_years:
        return None
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None
    
    # Calculate from project creation date
    deletion_date = project.created_at + relativedelta(years=retention_years, months=retention_months)
    
    return deletion_date


def get_selection_limit_info(project_id: int, user_id: str, db: Session) -> Dict[str, Any]:
    """
    Get information about photo selection limits for display to user.
    
    Returns:
        Dict with limit, current_count, remaining, percentage_used
    """
    restrictions = get_package_restrictions(project_id, db)
    
    if not restrictions or 'photo_selection_limit' not in restrictions:
        return {
            "has_limit": False,
            "limit": None,
            "current_count": 0,
            "remaining": None,
            "percentage_used": 0,
        }
    
    limit = restrictions['photo_selection_limit']
    
    # Count current selections
    current_count = db.query(UserPhotoSelection).join(Photo).filter(
        Photo.project_id == project_id,
        UserPhotoSelection.user_id == user_id
    ).count()
    
    remaining = max(0, limit - current_count)
    percentage_used = (current_count / limit * 100) if limit > 0 else 0
    
    return {
        "has_limit": True,
        "limit": limit,
        "current_count": current_count,
        "remaining": remaining,
        "percentage_used": round(percentage_used, 1),
        "is_at_limit": current_count >= limit,
    }


def create_package_snapshot(package_id: str, db: Session) -> Dict[str, Any]:
    """
    Create a snapshot of package configuration for freezing at project creation.
    
    Returns:
        Dict containing package name, restrictions, deliverables, lifecycle_config
    """
    package = db.query(ServicePackage).filter(ServicePackage.id == package_id).first()
    if not package:
        return {}
    
    restrictions = json.loads(package.restrictions) if isinstance(package.restrictions, str) and package.restrictions else package.restrictions or {}
    deliverables = json.loads(package.deliverables) if isinstance(package.deliverables, str) and package.deliverables else package.deliverables or []
    lifecycle_config = json.loads(package.lifecycle_config) if isinstance(package.lifecycle_config, str) and package.lifecycle_config else package.lifecycle_config or {}
    
    return {
        "package_id": package.id,
        "package_name": package.name,
        "package_category": package.category,
        "package_price": float(package.price),
        "restrictions": restrictions,
        "deliverables": deliverables,
        "lifecycle_config": lifecycle_config,
        "snapshot_created_at": datetime.now().isoformat(),
    }
