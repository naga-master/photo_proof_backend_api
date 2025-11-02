"""Photo upload router with presigned URLs."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.schemas import UserRead
from app.services.storage_service import get_storage_service
from app.services.upload_service import UploadService
from app.schemas.photo import (
    PresignedUploadRequest,
    PresignedUploadResponse,
    PhotoResponse,
)


router = APIRouter(tags=["Upload"])


@router.post("/presigned", response_model=PresignedUploadResponse)
def generate_presigned_upload(
    request: PresignedUploadRequest,
    user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate presigned URL for photo upload.
    
    Client flow:
    1. Call this endpoint to get upload URL and token
    2. Upload file directly to the returned URL using PUT
    3. Photo record is automatically created
    """
    storage = get_storage_service()
    upload_service = UploadService(storage)
    
    try:
        upload_token, upload_url = upload_service.generate_upload_token(
            db=db,
            project_id=request.project_id,
            filename=request.filename,
            content_type=request.content_type,
            file_size=request.file_size,
            user_id=user.id,
            folder_id=request.folder_id,
        )
        
        return PresignedUploadResponse(
            upload_url=upload_url,
            photo_id=0,  # Will be created on upload completion
            token=upload_token.token,
            expires_at=upload_token.expires_at,
            method="PUT",
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{token}", response_model=PhotoResponse)
async def complete_upload(
    token: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Complete photo upload using presigned token.
    
    This endpoint is called with the file data after getting presigned URL.
    It validates the token, saves the file, and creates the Photo record.
    """
    storage = get_storage_service()
    upload_service = UploadService(storage)
    
    try:
        # Read file data
        file_data = await file.read()
        
        # Complete upload
        photo = await upload_service.complete_upload(
            db=db,
            token=token,
            file_data=file_data,
        )
        
        return PhotoResponse(
            id=photo.id,
            project_id=photo.project_id,
            folder_id=photo.folder_id,
            src=photo.src,
            alt=photo.alt,
            original_filename=photo.original_filename,
            width=photo.width,
            height=photo.height,
            file_size=photo.file_size,
            mime_type=photo.mime_type,
            thumbnail_path=photo.thumbnail_path,
            order_index=photo.order_index,
            comment_count=photo.comment_count,
            status=photo.status,
            uploaded_by=photo.uploaded_by,
            created_at=photo.created_at,
            updated_at=photo.updated_at,
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.post("/session")
def create_upload_session(
    project_id: int,
    total_files: int,
    user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create batch upload session for progress tracking."""
    storage = get_storage_service()
    upload_service = UploadService(storage)
    
    session = upload_service.create_upload_session(
        db=db,
        project_id=project_id,
        user_id=user.id,
        total_files=total_files,
    )
    
    return {
        "session_id": session.id,
        "project_id": session.project_id,
        "total_files": session.total_files,
        "uploaded_files": session.uploaded_files,
        "status": session.status,
    }


@router.patch("/session/{session_id}")
def update_upload_session(
    session_id: int,
    uploaded_count: int,
    user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update upload session progress."""
    storage = get_storage_service()
    upload_service = UploadService(storage)
    
    try:
        session = upload_service.update_upload_progress(
            db=db,
            session_id=session_id,
            uploaded_count=uploaded_count,
        )
        
        return {
            "session_id": session.id,
            "total_files": session.total_files,
            "uploaded_files": session.uploaded_files,
            "status": session.status,
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
