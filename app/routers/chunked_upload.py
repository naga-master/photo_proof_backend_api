"""
Chunked Upload Router

RESTful endpoints for chunked file uploads.
"""

from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.schemas import UserRead
from app.services.storage_service import get_storage_service
from app.services.chunked_upload_service import ChunkedUploadService
from app.schemas.photo import PhotoResponse


router = APIRouter(prefix="/chunked", tags=["Chunked Upload"])


@router.post("/init")
def initialize_chunked_upload(
    request: Dict,
    user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initialize a chunked upload session.
    
    Request body:
    {
        "filename": "image.jpg",
        "fileSize": 104857600,
        "mimeType": "image/jpeg",
        "projectId": 1,
        "folderId": "uuid",
        "totalChunks": 50
    }
    
    Response:
    {
        "sessionId": "uuid",
        "photoId": 0,
        "totalChunks": 50
    }
    """
    storage = get_storage_service()
    upload_service = ChunkedUploadService(storage)
    
    try:
        session = upload_service.initialize_session(
            db=db,
            filename=request['filename'],
            file_size=request['fileSize'],
            mime_type=request['mimeType'],
            project_id=request['projectId'],
            folder_id=request.get('folderId'),
            user_id=user.id,
            total_chunks=request['totalChunks'],
        )
        
        return {
            "sessionId": session.session_id,
            "photoId": 0,  # Will be created on finalize
            "totalChunks": session.total_chunks,
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize upload: {str(e)}"
        )


@router.put("/{session_id}/{chunk_index}")
async def upload_chunk(
    session_id: str,
    chunk_index: int,
    chunk: UploadFile = File(...),
    index: str = Form(...),
    hash: str = Form(None),
    user: UserRead = Depends(get_current_user),
):
    """
    Upload a single chunk.
    
    Path parameters:
    - session_id: Upload session UUID
    - chunk_index: Index of this chunk (0-based)
    
    Form data:
    - chunk: Chunk file data
    - index: Chunk index (for verification)
    - hash: SHA-256 hash of chunk (optional, for verification)
    
    Response:
    {
        "sessionId": "uuid",
        "chunkIndex": 0,
        "status": "received",
        "uploadedChunks": 1,
        "totalChunks": 50
    }
    """
    storage = get_storage_service()
    upload_service = ChunkedUploadService(storage)
    
    try:
        # Read chunk data
        chunk_data = await chunk.read()
        
        # Verify index matches
        if int(index) != chunk_index:
            raise ValueError(f"Chunk index mismatch: path {chunk_index}, form {index}")
        
        # Receive chunk
        result = await upload_service.receive_chunk(
            session_id=session_id,
            chunk_index=chunk_index,
            chunk_data=chunk_data,
            chunk_hash=hash if hash else None,
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload chunk: {str(e)}"
        )


@router.post("/{session_id}/finalize", response_model=PhotoResponse)
async def finalize_chunked_upload(
    session_id: str,
    user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Finalize chunked upload by assembling chunks and creating Photo record.
    
    Path parameters:
    - session_id: Upload session UUID
    
    Response: PhotoResponse with completed photo
    """
    storage = get_storage_service()
    upload_service = ChunkedUploadService(storage)
    
    try:
        # Finalize upload
        photo = await upload_service.finalize_upload(
            db=db,
            session_id=session_id,
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
            detail=f"Failed to finalize upload: {str(e)}"
        )


@router.get("/{session_id}/status")
def get_upload_status(
    session_id: str,
    user: UserRead = Depends(get_current_user),
):
    """
    Get status of a chunked upload session.
    
    Response:
    {
        "sessionId": "uuid",
        "filename": "image.jpg",
        "totalChunks": 50,
        "uploadedChunks": 25,
        "status": "uploading",
        "createdAt": "2025-11-16T10:00:00"
    }
    """
    storage = get_storage_service()
    upload_service = ChunkedUploadService(storage)
    
    session = upload_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    return {
        "sessionId": session.session_id,
        "filename": session.filename,
        "fileSize": session.file_size,
        "totalChunks": session.total_chunks,
        "uploadedChunks": len(session.uploaded_chunks),
        "status": session.status,
        "createdAt": session.created_at.isoformat(),
        "expiresAt": session.expires_at.isoformat(),
    }
