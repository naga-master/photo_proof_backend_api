"""Project Member Service for managing team assignments."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models import ProjectMember, Project, User


class ProjectMemberService:
    """Service for managing project team memberships."""

    def __init__(self, db: Session):
        self.db = db

    def assign_user(
        self,
        project_id: int,
        user_id: str,
        role: str = "editor",
        assigned_by: Optional[str] = None
    ) -> ProjectMember:
        """
        Assign a user to a project.
        
        Args:
            project_id: The project to assign to
            user_id: The user to assign
            role: 'owner', 'editor', or 'viewer'
            assigned_by: The user making the assignment
            
        Returns:
            The created ProjectMember record
        """
        # Check if already assigned
        existing = self.db.query(ProjectMember).filter(
            and_(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            )
        ).first()
        
        if existing:
            # Update role if already assigned
            existing.role = role
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        # Create new assignment
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role,
            assigned_by=assigned_by
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def remove_user(self, project_id: int, user_id: str) -> bool:
        """
        Remove a user from a project.
        
        Returns:
            True if removed, False if not found
        """
        member = self.db.query(ProjectMember).filter(
            and_(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            )
        ).first()
        
        if not member:
            return False
        
        self.db.delete(member)
        self.db.commit()
        return True

    def get_project_members(self, project_id: int) -> List[ProjectMember]:
        """Get all members assigned to a project."""
        return self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id
        ).all()

    def get_user_projects(self, user_id: str) -> List[int]:
        """Get list of project IDs a user is assigned to."""
        memberships = self.db.query(ProjectMember.project_id).filter(
            ProjectMember.user_id == user_id
        ).all()
        return [m.project_id for m in memberships]

    def can_access_project(self, user_id: str, project_id: int) -> bool:
        """
        Check if a user can access a project.
        
        Returns True if:
        - User is assigned to the project
        - User is studio owner/admin (checked separately in permission layer)
        """
        return self.db.query(ProjectMember).filter(
            and_(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            )
        ).first() is not None

    def get_member_role(self, user_id: str, project_id: int) -> Optional[str]:
        """Get the user's role in a project, or None if not assigned."""
        member = self.db.query(ProjectMember).filter(
            and_(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            )
        ).first()
        return member.role if member else None

    def is_project_owner(self, user_id: str, project_id: int) -> bool:
        """Check if user is the project owner."""
        return self.get_member_role(user_id, project_id) == "owner"

    def get_members_with_users(self, project_id: int) -> List[dict]:
        """
        Get project members with user details.
        
        Returns list of dicts with member info and user details.
        """
        members = self.db.query(ProjectMember, User).join(
            User, ProjectMember.user_id == User.id
        ).filter(
            ProjectMember.project_id == project_id
        ).all()
        
        return [
            {
                "id": member.id,
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "role": member.role,
                "assigned_at": member.assigned_at.isoformat() if member.assigned_at else None,
            }
            for member, user in members
        ]
