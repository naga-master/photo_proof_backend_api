"""Selection status endpoints for package restriction enforcement."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.db.models import User, Project
from app.middleware.package_restrictions import get_selection_limit_info


router = APIRouter()


@router.get("/projects/{project_id}/selection-status")
def get_project_selection_status(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get photo selection status for a project.
    
    Returns information about selection limits and current usage.
    Used by client UI to show selection counter.
    """
    # Verify project exists and user has access
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check access
    if current_user.studio_id != project.studio_id:
        if not current_user.client_profile or project.client_id != current_user.client_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
    
    # Get selection limit info
    info = get_selection_limit_info(project_id, current_user.id, db)
    
    return {
        "project_id": project_id,
        "user_id": current_user.id,
        **info
    }
