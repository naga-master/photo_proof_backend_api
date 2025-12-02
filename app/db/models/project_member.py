"""ProjectMember model for team assignment to projects."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class ProjectMember(Base):
    """
    Associates users with specific projects for access control.
    
    Roles:
    - 'owner': Full control over project (usually studio owner or creator)
    - 'editor': Can view and edit project content
    - 'viewer': Read-only access
    """
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), default="editor")  # 'owner', 'editor', 'viewer'
    assigned_at = Column(DateTime, server_default=func.now())
    assigned_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], back_populates="project_memberships")
    assigner = relationship("User", foreign_keys=[assigned_by])

    def __repr__(self):
        return f"<ProjectMember(project_id={self.project_id}, user_id={self.user_id}, role={self.role})>"
