"""
Photo Proof API - Main FastAPI Application

RESTful API for the photo proofing gallery system with comprehensive endpoints
for projects, images, categories, and comments.
"""

from fastapi import FastAPI, HTTPException, Depends, Query, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uuid
from datetime import datetime

from models import (
    Project, ProjectImage, ProjectCategory, Comment, User, Studio,
    CreateProjectRequest, CreateCategoryRequest, UpdateImageRequest, CreateCommentRequest,
    ProjectListResponse, ImageListResponse, CommentListResponse,
    ProjectStatus, UserRole, ImageVersion, ImageMetadata, ProjectSettings
)
from data_manager import data_manager

app = FastAPI(
    title="Photo Proof API",
    description="Professional photo proofing gallery system API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency for getting current user (simplified for demo)
async def get_current_user() -> User:
    """Get current authenticated user (simplified for demo)"""
    # In a real app, this would validate JWT tokens
    return data_manager.get_user_by_id("user-001")  # Default to studio user


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Photo Proof API is running", "version": "1.0.0"}


# Studio endpoints
@app.get("/api/studios", response_model=List[Studio])
async def get_studios():
    """Get all studios"""
    return data_manager.get_studios()


@app.get("/api/studios/{studio_id}", response_model=Studio)
async def get_studio(studio_id: str):
    """Get studio by ID"""
    studio = data_manager.get_studio_by_id(studio_id)
    if not studio:
        raise HTTPException(status_code=404, detail="Studio not found")
    return studio


# User endpoints
@app.get("/api/users/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@app.get("/api/users", response_model=List[User])
async def get_users():
    """Get all users"""
    return data_manager.get_users()


# Project endpoints
@app.get("/api/projects", response_model=ProjectListResponse)
async def get_projects(
    studio_id: Optional[str] = Query(None, description="Filter by studio ID"),
    status: Optional[ProjectStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user)
):
    """Get projects with optional filtering"""
    projects = data_manager.get_projects(studio_id=studio_id)
    
    # Filter by status if provided
    if status:
        projects = [p for p in projects if p.status == status]
    
    # Filter by user access rights
    if current_user.role == UserRole.CLIENT:
        # Clients can only see projects they have access to
        projects = [p for p in projects if p.client_email == current_user.email]
    elif current_user.role == UserRole.STUDIO and current_user.studio_id:
        # Studio users can only see their own studio's projects
        projects = [p for p in projects if p.studio_id == current_user.studio_id]
    
    return ProjectListResponse(projects=projects, total=len(projects))


@app.get("/api/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Get project by ID"""
    project = data_manager.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.get("/api/projects/access/{access_url}", response_model=Project)
async def get_project_by_access_url(access_url: str):
    """Get project by access URL (for client access)"""
    project = data_manager.get_project_by_access_url(access_url)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.post("/api/projects", response_model=Project)
async def create_project(
    request: CreateProjectRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new project"""
    if current_user.role != UserRole.STUDIO:
        raise HTTPException(status_code=403, detail="Only studio users can create projects")
    
    project_id = str(uuid.uuid4())
    access_url = f"{request.name.lower().replace(' ', '-')}-{str(uuid.uuid4())[:8]}"
    
    # Use provided categories or default ones
    categories = request.categories or [
        ProjectCategory(
            id="candid",
            name="candid",
            display_name="Candid",
            description="Natural, unposed moments",
            order=1,
            is_default=True
        ),
        ProjectCategory(
            id="portrait",
            name="portrait",
            display_name="Portrait",
            description="Formal portraits and posed shots",
            order=2,
            is_default=True
        ),
        ProjectCategory(
            id="traditional",
            name="traditional",
            display_name="Traditional",
            description="Traditional ceremony and formal events",
            order=3,
            is_default=True
        ),
    ]
    
    project = Project(
        id=project_id,
        name=request.name,
        description=request.description,
        client_name=request.client_name,
        client_email=request.client_email,
        studio_id=current_user.studio_id,
        categories=categories,
        images=[],
        settings={
            "is_password_protected": False,
            "allow_downloads": True,
            "allow_comments": True
        },
        status=ProjectStatus.DRAFT,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        access_url=access_url
    )
    
    return data_manager.create_project(project)


# Category endpoints
@app.get("/api/projects/{project_id}/categories", response_model=List[ProjectCategory])
async def get_project_categories(project_id: str):
    """Get categories for a project"""
    project = data_manager.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.categories


@app.post("/api/projects/{project_id}/categories", response_model=ProjectCategory)
async def create_project_category(
    project_id: str,
    request: CreateCategoryRequest,
    current_user: User = Depends(get_current_user)
):
    """Add a new category to a project"""
    if current_user.role != UserRole.STUDIO:
        raise HTTPException(status_code=403, detail="Only studio users can create categories")
    
    project = data_manager.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if category name already exists
    if any(cat.name.lower() == request.name.lower() for cat in project.categories):
        raise HTTPException(status_code=400, detail="Category already exists")
    
    category = ProjectCategory(
        id=str(uuid.uuid4()),
        name=request.name.lower().replace(' ', '-'),
        display_name=request.display_name,
        description=request.description,
        order=len(project.categories) + 1
    )
    
    updated_project = data_manager.add_category_to_project(project_id, category)
    if not updated_project:
        raise HTTPException(status_code=400, detail="Failed to add category")
    
    return category


# Image endpoints
@app.get("/api/projects/{project_id}/images", response_model=ImageListResponse)
async def get_project_images(
    project_id: str,
    category_id: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=200, description="Number of images to return"),
    offset: int = Query(0, ge=0, description="Number of images to skip")
):
    """Get images for a project, optionally filtered by category"""
    project = data_manager.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    images = project.images
    
    # Filter by category if provided
    if category_id:
        images = [img for img in images if img.category_id == category_id]
    
    # Apply pagination
    total = len(images)
    images = images[offset:offset + limit]
    
    return ImageListResponse(
        images=images,
        total=total,
        category_id=category_id or "all"
    )


@app.get("/api/projects/{project_id}/images/{image_id}", response_model=ProjectImage)
async def get_project_image(project_id: str, image_id: str):
    """Get a specific image"""
    project = data_manager.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    image = next((img for img in project.images if img.id == image_id), None)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    return image


@app.patch("/api/projects/{project_id}/images/{image_id}", response_model=ProjectImage)
async def update_project_image(
    project_id: str,
    image_id: str,
    request: UpdateImageRequest,
    current_user: User = Depends(get_current_user)
):
    """Update image properties (selection, favorite, tags)"""
    # Build update dict from non-None values
    updates = {}
    if request.is_selected is not None:
        updates["is_selected"] = request.is_selected
    if request.is_favorite is not None:
        updates["is_favorite"] = request.is_favorite
    if request.tags is not None:
        updates["tags"] = request.tags
    
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    image = data_manager.update_project_image(project_id, image_id, updates)
    if not image:
        raise HTTPException(status_code=404, detail="Image or project not found")
    
    return image


# Comment endpoints
@app.get("/api/projects/{project_id}/images/{image_id}/comments", response_model=CommentListResponse)
async def get_image_comments(project_id: str, image_id: str):
    """Get comments for an image"""
    project = data_manager.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify image exists
    image = next((img for img in project.images if img.id == image_id), None)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    comments = data_manager.get_comments(image_id=image_id)
    return CommentListResponse(
        comments=comments,
        total=len(comments),
        image_id=image_id
    )


@app.post("/api/projects/{project_id}/images/{image_id}/comments", response_model=Comment)
async def create_image_comment(
    project_id: str,
    image_id: str,
    request: CreateCommentRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a comment on an image"""
    project = data_manager.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify image exists
    image = next((img for img in project.images if img.id == image_id), None)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    comment = Comment(
        id=str(uuid.uuid4()),
        image_id=image_id,
        project_id=project_id,
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role,
        content=request.content,
        parent_id=request.parent_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    return data_manager.create_comment(comment)


# Statistics endpoints
@app.get("/api/projects/{project_id}/stats")
async def get_project_stats(project_id: str):
    """Get project statistics"""
    project = data_manager.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    total_images = len(project.images)
    selected_images = len([img for img in project.images if img.is_selected])
    favorite_images = len([img for img in project.images if img.is_favorite])
    total_comments = sum(img.comment_count for img in project.images)
    
    # Category breakdown
    category_stats = {}
    for category in project.categories:
        category_images = [img for img in project.images if img.category_id == category.id]
        category_stats[category.id] = {
            "name": category.display_name,
            "total_images": len(category_images),
            "selected_images": len([img for img in category_images if img.is_selected]),
            "favorite_images": len([img for img in category_images if img.is_favorite])
        }
    
    return {
        "project_id": project_id,
        "total_images": total_images,
        "selected_images": selected_images,
        "favorite_images": favorite_images,
        "total_comments": total_comments,
        "categories": category_stats
    }


@app.get("/api/studio/{studio_id}/dashboard")
async def get_studio_dashboard(studio_id: str, current_user: User = Depends(get_current_user)):
    """Get studio dashboard statistics without loading ANY image data"""
    
    # Verify access
    if current_user.role != UserRole.STUDIO or current_user.studio_id != studio_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Use optimized stats method that never loads image URLs
    stats_data = data_manager.get_studio_stats(studio_id)
    
    return {
        "studio_id": studio_id,
        "stats": {
            "total_projects": stats_data["total_projects"],
            "active_projects": stats_data["active_projects"],
            "total_images": stats_data["total_images"],
            "total_clients": stats_data["total_clients"],
            "total_comments": stats_data["total_comments"]
        },
        "recent_projects": stats_data["recent_projects"]
    }


# Upload endpoints
@app.post("/api/projects/{project_id}/upload")
async def upload_images(
    project_id: str,
    files: List[UploadFile] = File(...),
    category_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Upload images to a project"""
    if current_user.role != UserRole.STUDIO:
        raise HTTPException(status_code=403, detail="Only studio users can upload images")
    
    project = data_manager.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Default to first category if not specified
    if not category_id and project.categories:
        category_id = project.categories[0].id
    
    uploaded_images = []
    
    for file in files:
        # Validate file type
        if not file.content_type.startswith('image/'):
            continue
        
        # Create image record (in real app, would save file to storage)
        image_id = str(uuid.uuid4())
        
        # Create mock image version (in real app, would process and store file)
        version = ImageVersion(
            id=f"ver-{image_id}",
            version="original",
            url=f"https://picsum.photos/800/600?random={len(project.images) + 1}",
            thumbnail=f"https://picsum.photos/300/200?random={len(project.images) + 1}",
            file_name=file.filename,
            uploaded_at=datetime.now(),
            is_latest=True,
            file_size=1024 * 1024  # Mock file size
        )
        
        image = ProjectImage(
            id=image_id,
            original_file_name=file.filename,
            category_id=category_id,
            versions=[version],
            metadata=ImageMetadata(
                width=3840,
                height=2560,
                camera="Uploaded Camera",
                lens="Uploaded Lens"
            ),
            tags=[],
            is_selected=False,
            is_favorite=False,
            comment_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Add image to project
        data_manager.add_image_to_project(project_id, image)
        uploaded_images.append(image)
    
    return {"message": f"Uploaded {len(uploaded_images)} images", "images": uploaded_images}


# Settings endpoints
@app.get("/api/settings/studio/{studio_id}")
async def get_studio_settings(
    studio_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get studio settings"""
    if current_user.role != UserRole.STUDIO or current_user.studio_id != studio_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    studio = data_manager.get_studio_by_id(studio_id)
    if not studio:
        raise HTTPException(status_code=404, detail="Studio not found")
    
    # Return mock settings (in real app, would be stored in database)
    return {
        "studio_id": studio_id,
        "studio_name": studio.name,
        "settings": {
            "default_allow_downloads": True,
            "default_allow_comments": True,
            "watermark_enabled": False,
            "auto_backup": True,
            "notification_email": studio.email,
            "timezone": "America/New_York",
            "default_categories": [
                {"name": "candid", "display_name": "Candid"},
                {"name": "portrait", "display_name": "Portrait"},
                {"name": "traditional", "display_name": "Traditional"}
            ]
        }
    }


@app.put("/api/settings/studio/{studio_id}")
async def update_studio_settings(
    studio_id: str,
    settings: dict,
    current_user: User = Depends(get_current_user)
):
    """Update studio settings"""
    if current_user.role != UserRole.STUDIO or current_user.studio_id != studio_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    studio = data_manager.get_studio_by_id(studio_id)
    if not studio:
        raise HTTPException(status_code=404, detail="Studio not found")
    
    # In real app, would save settings to database
    return {"message": "Settings updated successfully", "settings": settings}


# Project settings endpoints
@app.get("/api/projects/{project_id}/settings")
async def get_project_settings(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get project settings"""
    project = data_manager.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project.settings


@app.put("/api/projects/{project_id}/settings")
async def update_project_settings(
    project_id: str,
    settings: ProjectSettings,
    current_user: User = Depends(get_current_user)
):
    """Update project settings"""
    if current_user.role != UserRole.STUDIO:
        raise HTTPException(status_code=403, detail="Only studio users can update project settings")
    
    updated_project = data_manager.update_project_settings(project_id, settings)
    if not updated_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return updated_project.settings


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
