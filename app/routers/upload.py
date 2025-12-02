"""Photo upload router with presigned URLs."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.schemas import UserRead
from app.services.storage_service import get_storage_service
from app.services.upload_service import UploadService, _process_photo_variants_background
from app.schemas.photo import (
    PresignedUploadRequest,
    PresignedUploadResponse,
    BatchPresignedUploadRequest,
    BatchPresignedUploadResponse,
    PhotoResponse,
)
from app.core.permissions import require_upload_photos

# Import chunked upload router
from app.routers.chunked_upload import router as chunked_upload_router


router = APIRouter(tags=["Upload"])

# Include chunked upload routes
router.include_router(chunked_upload_router)


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
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Complete photo upload using presigned token.
    
    This endpoint is called with the file data after getting presigned URL.
    It validates the token, saves the file, creates the Photo record, and
    queues background processing for image variants.
    """
    storage = get_storage_service()
    upload_service = UploadService(storage)
    
    try:
        # Read file data
        file_data = await file.read()
        
        # Complete upload (returns immediately with status='processing')
        photo = await upload_service.complete_upload(
            db=db,
            token=token,
            file_data=file_data,
        )
        
        # Queue background processing for variants
        background_tasks.add_task(
            _process_photo_variants_background,
            photo_id=photo.id,
            storage_path=photo.storage_path,
            project_id=photo.project_id
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
    
    except HTTPException as e:
        # Re-raise HTTP exceptions as-is (e.g., 409 for duplicates)
        raise e
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
    
    # Get values from upload_rules JSON
    upload_rules = session.upload_rules or {}
    
    return {
        "session_id": session.id,
        "project_id": session.project_id,
        "total_files": upload_rules.get('total_files', 0),
        "uploaded_files": upload_rules.get('uploaded_files', 0),
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
        
        # Get values from upload_rules JSON
        upload_rules = session.upload_rules or {}
        
        return {
            "session_id": session.id,
            "total_files": upload_rules.get('total_files', 0),
            "uploaded_files": upload_rules.get('uploaded_files', 0),
            "status": session.status,
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/batch/presigned", response_model=BatchPresignedUploadResponse)
def generate_batch_presigned_urls(
    request: BatchPresignedUploadRequest,
    user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate batch presigned URLs for multiple photo uploads.
    
    This endpoint creates a single upload session and generates presigned URLs
    for all files in the batch, reducing the number of API calls.
    
    Client flow:
    1. Call this endpoint once with all file metadata
    2. Receive array of presigned URLs and tokens
    3. Upload each file to its corresponding URL using PUT
    4. Optionally call verification endpoint to check batch status
    """
    storage = get_storage_service()
    upload_service = UploadService(storage)
    
    try:
        # Validate file count
        if len(request.files) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 100 files per batch"
            )
        
        # Generate batch tokens
        upload_session, tokens_and_urls = upload_service.generate_batch_upload_tokens(
            db=db,
            project_id=request.project_id,
            files=request.files,
            user_id=user.id,
            folder_id=request.folder_id,
        )
        
        # Build response
        token_responses = []
        for upload_token, upload_url in tokens_and_urls:
            token_responses.append(
                PresignedUploadResponse(
                    upload_url=upload_url,
                    photo_id=0,  # Will be created on upload completion
                    token=upload_token.token,
                    expires_at=upload_token.expires_at,
                    method="PUT",
                )
            )
        
        # Get total_files from upload_rules JSON
        upload_rules = upload_session.upload_rules or {}
        total_files = upload_rules.get('total_files', len(request.files))
        
        return BatchPresignedUploadResponse(
            tokens=token_responses,
            session_id=upload_session.id,
            total_files=total_files,
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/batch/verify/{session_id}")
async def verify_batch_upload(
    session_id: int,
    user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify batch upload completion status.
    
    Returns summary of upload status including:
    - Total files in batch
    - Completed uploads
    - Failed uploads
    - Pending uploads
    """
    storage = get_storage_service()
    upload_service = UploadService(storage)
    
    try:
        summary = await upload_service.complete_batch_upload_verification(
            db=db,
            session_id=session_id,
        )
        
        return summary
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
