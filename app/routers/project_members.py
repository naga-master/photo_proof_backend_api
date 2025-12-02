"""Project Members router for managing team assignments."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db
from app.db.models import User, Project, ProjectMember
from app.api.deps import get_current_user
from app.services.project_member_service import ProjectMemberService
from app.services.permission_service import PermissionService


router = APIRouter()


# Schemas
class ProjectMemberCreate(BaseModel):
    user_id: str
    role: str = "editor"  # 'owner', 'editor', 'viewer'


class ProjectMemberResponse(BaseModel):
    id: int
    user_id: str
    name: str
    email: str
    role: str
    assigned_at: str | None = None

    class Config:
        from_attributes = True


class ProjectMemberListResponse(BaseModel):
    members: List[ProjectMemberResponse]
    total: int


def _check_can_manage_members(current_user: User, project: Project, db: Session) -> bool:
    """Check if user can manage project members."""
    # Studio owner can manage all
    if current_user.role == "studio_owner":
        return True
    
    # Studio admin can manage all in their studio
    if current_user.role == "studio_admin" and current_user.studio_id == project.studio_id:
        return True
    
    # Check if user has canManageUsers permission
    if PermissionService.has_permission(current_user, "canManageUsers"):
        return True
    
    # Project owner can manage their project
    service = ProjectMemberService(db)
    if service.is_project_owner(current_user.id, project.id):
        return True
    
    return False


@router.get("/projects/{project_id}/members", response_model=ProjectMemberListResponse)
def list_project_members(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all members assigned to a project.
    
    Requires:
    - User must be in the same studio
    - User must have access to the project
    """
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check studio access
    if current_user.studio_id != project.studio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this project"
        )
    
    # Get members with user details
    service = ProjectMemberService(db)
    members = service.get_members_with_users(project_id)
    
    return ProjectMemberListResponse(
        members=[ProjectMemberResponse(**m) for m in members],
        total=len(members)
    )


@router.post("/projects/{project_id}/members", response_model=ProjectMemberResponse, status_code=status.HTTP_201_CREATED)
def add_project_member(
    project_id: int,
    member_data: ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add a user to a project team.
    
    Requires:
    - Studio owner, admin, or project owner
    - Target user must be in the same studio
    """
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permission to manage members
    if not _check_can_manage_members(current_user, project, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage project members"
        )
    
    # Check target user exists and is in same studio
    target_user = db.query(User).filter(User.id == member_data.user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if target_user.studio_id != project.studio_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be in the same studio"
        )
    
    # Validate role
    if member_data.role not in ["owner", "editor", "viewer"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'owner', 'editor', or 'viewer'"
        )
    
    # Assign user
    service = ProjectMemberService(db)
    member = service.assign_user(
        project_id=project_id,
        user_id=member_data.user_id,
        role=member_data.role,
        assigned_by=current_user.id
    )
    
    return ProjectMemberResponse(
        id=member.id,
        user_id=target_user.id,
        name=target_user.name,
        email=target_user.email,
        role=member.role,
        assigned_at=member.assigned_at.isoformat() if member.assigned_at else None
    )


@router.patch("/projects/{project_id}/members/{user_id}", response_model=ProjectMemberResponse)
def update_project_member(
    project_id: int,
    user_id: str,
    member_data: ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a member's role in a project."""
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permission
    if not _check_can_manage_members(current_user, project, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage project members"
        )
    
    # Update role
    service = ProjectMemberService(db)
    member = service.assign_user(
        project_id=project_id,
        user_id=user_id,
        role=member_data.role,
        assigned_by=current_user.id
    )
    
    target_user = db.query(User).filter(User.id == user_id).first()
    
    return ProjectMemberResponse(
        id=member.id,
        user_id=target_user.id,
        name=target_user.name,
        email=target_user.email,
        role=member.role,
        assigned_at=member.assigned_at.isoformat() if member.assigned_at else None
    )


@router.delete("/projects/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project_member(
    project_id: int,
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove a user from a project team.
    
    Note: Cannot remove the last owner unless you're studio owner/admin.
    """
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permission
    if not _check_can_manage_members(current_user, project, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage project members"
        )
    
    # Check if removing the last owner
    service = ProjectMemberService(db)
    member_role = service.get_member_role(user_id, project_id)
    
    if member_role == "owner":
        # Count owners
        owners = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.role == "owner"
        ).count()
        
        if owners <= 1 and current_user.role not in ["studio_owner", "studio_admin"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last project owner"
            )
    
    # Remove member
    success = service.remove_user(project_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in project"
        )
    
    return None
