"""
TEMPLATE ROUTER - CRUD Pattern for Projects

This template demonstrates the standard CRUD (Create, Read, Update, Delete) pattern
used throughout the Photo Proof API. Use this as a reference to implement similar
routers for other entities.

Pattern applies to:
- Clients router (/api/clients)
- Folders router (/api/folders)
- Products router (/api/products)
- Cart router (/api/cart)
- Orders router (/api/orders)
- Invoices router (/api/invoices)
- Service Packages router (/api/packages)
- Layout Templates router (/api/layouts)
- Notifications router (/api/notifications)
- Analytics router (/api/analytics)

Key principles:
1. Authentication: All endpoints require authentication via HTTPBearer token
2. Authorization: Check user permissions (studio_id, client_id) before operations
3. Error handling: Use HTTPException with appropriate status codes
4. Response models: Use Pydantic schemas for type safety
5. Database sessions: Use `get_db` dependency for SQLAlchemy session
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.services.auth_service import AuthService
from app.db.models import Project, Photo, Folder
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
)


router = APIRouter(prefix="/api/projects", tags=["Projects"])
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Dependency to get current authenticated user."""
    token = credentials.credentials
    user_data = AuthService.get_current_user(db, token)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return user_data


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreate,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new project.
    
    Pattern: POST /api/resource
    - Validate user permissions (studio only can create)
    - Create new record
    - Return created record with 201 status
    """
    # Authorization check
    if user["role"] != "studio":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studio users can create projects"
        )
    
    try:
        project = Project(
            title=project_data.title,
            studio_id=user["id"],
            client_id=project_data.client_id,
            shoot_date=project_data.shoot_date,
            layout=project_data.layout,
            is_locked=project_data.is_locked,
            package_id=project_data.package_id,
            status="draft",
            photo_count=0,
            has_folders=False,
        )
        
        db.add(project)
        db.commit()
        db.refresh(project)
        
        return ProjectResponse(
            id=project.id,
            title=project.title,
            studio_id=project.studio_id,
            client_id=project.client_id,
            shoot_date=project.shoot_date,
            layout=project.layout,
            cover_photo_id=project.cover_photo_id,
            cover_photo_src=None,
            photo_count=project.photo_count,
            is_locked=project.is_locked,
            payment_status=project.payment_status,
            price=project.price,
            package_id=project.package_id,
            status=project.status,
            has_folders=project.has_folders,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=ProjectListResponse)
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List projects with pagination and filtering.
    
    Pattern: GET /api/resource
    - Filter by user permissions (studio sees all, client sees only theirs)
    - Apply query parameters (pagination, filters)
    - Return list with total count
    """
    # Build query based on user role
    query = db.query(Project)
    
    if user["role"] == "studio":
        # Studio sees all their projects
        query = query.filter(Project.studio_id == user["id"])
    
    elif user["role"] == "client":
        # Client sees only their projects
        query = query.filter(Project.client_id == user.get("client_id"))
    
    # Apply filters
    if status:
        query = query.filter(Project.status == status)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    projects = query.offset(skip).limit(limit).all()
    
    # Build responses
    project_responses = []
    for project in projects:
        # Get cover photo if exists
        cover_photo_src = None
        if project.cover_photo_id:
            photo = db.query(Photo).filter(Photo.id == project.cover_photo_id).first()
            if photo:
                cover_photo_src = photo.src
        
        project_responses.append(ProjectResponse(
            id=project.id,
            title=project.title,
            studio_id=project.studio_id,
            client_id=project.client_id,
            shoot_date=project.shoot_date,
            layout=project.layout,
            cover_photo_id=project.cover_photo_id,
            cover_photo_src=cover_photo_src,
            photo_count=project.photo_count,
            is_locked=project.is_locked,
            payment_status=project.payment_status,
            price=project.price,
            package_id=project.package_id,
            status=project.status,
            has_folders=project.has_folders,
            created_at=project.created_at,
            updated_at=project.updated_at,
        ))
    
    return ProjectListResponse(
        projects=project_responses,
        total=total
    )


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get single project by ID.
    
    Pattern: GET /api/resource/{id}
    - Verify resource exists
    - Check user permissions
    - Return detailed resource
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Authorization check
    if user["role"] == "studio" and project.studio_id != user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if user["role"] == "client" and project.client_id != user.get("client_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get cover photo
    cover_photo_src = None
    if project.cover_photo_id:
        photo = db.query(Photo).filter(Photo.id == project.cover_photo_id).first()
        if photo:
            cover_photo_src = photo.src
    
    return ProjectResponse(
        id=project.id,
        title=project.title,
        studio_id=project.studio_id,
        client_id=project.client_id,
        shoot_date=project.shoot_date,
        layout=project.layout,
        cover_photo_id=project.cover_photo_id,
        cover_photo_src=cover_photo_src,
        photo_count=project.photo_count,
        is_locked=project.is_locked,
        payment_status=project.payment_status,
        price=project.price,
        package_id=project.package_id,
        status=project.status,
        has_folders=project.has_folders,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update project.
    
    Pattern: PATCH /api/resource/{id}
    - Verify resource exists
    - Check user permissions
    - Update only provided fields
    - Return updated resource
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Authorization check - only studio can update
    if user["role"] != "studio" or project.studio_id != user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can update"
        )
    
    try:
        # Update only provided fields
        update_data = project_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)
        
        db.commit()
        db.refresh(project)
        
        # Get cover photo
        cover_photo_src = None
        if project.cover_photo_id:
            photo = db.query(Photo).filter(Photo.id == project.cover_photo_id).first()
            if photo:
                cover_photo_src = photo.src
        
        return ProjectResponse(
            id=project.id,
            title=project.title,
            studio_id=project.studio_id,
            client_id=project.client_id,
            shoot_date=project.shoot_date,
            layout=project.layout,
            cover_photo_id=project.cover_photo_id,
            cover_photo_src=cover_photo_src,
            photo_count=project.photo_count,
            is_locked=project.is_locked,
            payment_status=project.payment_status,
            price=project.price,
            package_id=project.package_id,
            status=project.status,
            has_folders=project.has_folders,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete project.
    
    Pattern: DELETE /api/resource/{id}
    - Verify resource exists
    - Check user permissions
    - Perform soft or hard delete
    - Return 204 No Content
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Authorization check - only studio can delete
    if user["role"] != "studio" or project.studio_id != user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can delete"
        )
    
    try:
        # Soft delete
        project.status = "archived"
        db.commit()
        
        # Or hard delete:
        # db.delete(project)
        # db.commit()
        
        return None
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{project_id}/folders")
def get_project_folders(
    project_id: int,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all folders for a project.
    
    Returns folders with cover photo information.
    """
    from sqlalchemy.orm import joinedload
    
    # Get project and verify access
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Authorization check
    if user["role"] == "studio":
        if project.studio_id != user["studio_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
    elif user["role"] == "client":
        if project.client_id != user.get("client_id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )
    
    # Get folders with cover photos
    folders = (
        db.query(Folder)
        .options(joinedload(Folder.cover_photo))
        .filter(Folder.project_id == project_id)
        .order_by(Folder.order_index, Folder.created_at)
        .all()
    )
    
    # Format response
    folder_list = []
    for folder in folders:
        cover_photo_src = None
        if folder.cover_photo:
            cover_photo_src = f"/uploads/{folder.cover_photo.storage_path}"
        
        folder_list.append({
            "id": folder.id,
            "name": folder.name,
            "project_id": folder.project_id,
            "photo_count": folder.photo_count,
            "cover_photo_id": folder.cover_photo_id,
            "cover_photo_src": cover_photo_src,
            "order_index": folder.order_index,
            "created_at": folder.created_at.isoformat() if folder.created_at else None,
            "updated_at": folder.updated_at.isoformat() if folder.updated_at else None,
        })
    
    return {
        "folders": folder_list,
        "total": len(folder_list)
    }
