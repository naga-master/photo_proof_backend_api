"""Comments router with nested reply support."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.schemas import UserRead
from app.services.comment_service import CommentService
from app.schemas.photo import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentListResponse,
)


router = APIRouter(tags=["Comments"])


@router.get("/photos/{photo_id}", response_model=CommentListResponse)
def get_photo_comments(
    photo_id: int,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all comments for a photo as nested tree structure.
    
    Returns:
    - Root comments with nested replies
    - Reply context (reply_to_author, reply_to_text) for WhatsApp-style display
    - Sorted: root comments newest first, replies oldest first (conversation flow)
    """
    try:
        comments_tree = CommentService.get_photo_comments(db, photo_id)
        
        return CommentListResponse(
            comments=comments_tree,
            total=len(comments_tree),
            photo_id=photo_id,
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch comments: {str(e)}"
        )


@router.post("/", response_model=CommentResponse)
def create_comment(
    comment_data: CommentCreate,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new comment or reply.
    
    For top-level comments:
    - Leave parent_comment_id and reply_to_id as None
    
    For replies:
    - Set parent_comment_id to the root comment (for storage hierarchy)
    - Set reply_to_id to the specific comment being replied to (for UI context)
    
    Example nested reply:
    - Comment A (root)
      - Reply B (parent_comment_id=A, reply_to_id=A)
      - Reply C (parent_comment_id=A, reply_to_id=B)  <- Replying to B
    """
    try:
        comment = CommentService.create_comment(
            db=db,
            photo_id=comment_data.photo_id,
            user_id=current_user.id,
            text=comment_data.text,
            parent_comment_id=comment_data.parent_comment_id,
            reply_to_id=comment_data.reply_to_id,
        )
        
        # Get user info for response
        user_info = CommentService.get_user_info(db, comment.user_id)
        
        # Get reply-to context if applicable
        reply_to_author = None
        reply_to_text = None
        if comment.reply_to_id:
            from app.db.models import Comment
            reply_to_comment = db.query(Comment).filter(Comment.id == comment.reply_to_id).first()
            if reply_to_comment:
                reply_to_info = CommentService.get_user_info(db, reply_to_comment.user_id)
                reply_to_author = reply_to_info["name"]
                reply_to_text = reply_to_comment.text[:50]
        
        return CommentResponse(
            id=comment.id,
            photo_id=comment.photo_id,
            user_id=comment.user_id,
            text=comment.text,
            author="Studio" if user_info["role"] == "studio" else "Client",
            user_name=user_info["name"],
            user_avatar=user_info["avatar"],
            parent_comment_id=comment.parent_comment_id,
            reply_to_id=comment.reply_to_id,
            reply_to_author=reply_to_author,
            reply_to_text=reply_to_text,
            is_edited=comment.is_edited,
            timestamp=CommentService._format_timestamp(comment.created_at),
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            replies=[],
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    comment_data: CommentUpdate,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a comment (only by original author)."""
    try:
        comment = CommentService.update_comment(
            db=db,
            comment_id=comment_id,
            user_id=current_user.id,
            text=comment_data.text,
        )
        
        user_info = CommentService.get_user_info(db, comment.user_id)
        
        return CommentResponse(
            id=comment.id,
            photo_id=comment.photo_id,
            user_id=comment.user_id,
            text=comment.text,
            author="Studio" if user_info["role"] == "studio" else "Client",
            user_name=user_info["name"],
            user_avatar=user_info["avatar"],
            parent_comment_id=comment.parent_comment_id,
            reply_to_id=comment.reply_to_id,
            is_edited=comment.is_edited,
            timestamp=CommentService._format_timestamp(comment.created_at),
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            replies=[],
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{comment_id}")
def delete_comment(
    comment_id: int,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete a comment (only by original author)."""
    try:
        success = CommentService.delete_comment(
            db=db,
            comment_id=comment_id,
            user_id=current_user.id,
        )
        
        return {"success": success, "message": "Comment deleted successfully"}
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
