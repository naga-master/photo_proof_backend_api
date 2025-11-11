"""Comment service with nested reply tree logic."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

from app.db.models import Comment, User, Client, Studio, Photo


class CommentService:
    """Comment service with nested reply tree building."""
    
    @staticmethod
    def create_comment(
        db: Session,
        photo_id: int,
        user_id: str,
        text: str,
        parent_comment_id: Optional[int] = None,
        reply_to_id: Optional[int] = None,
    ) -> Comment:
        """
        Create a new comment.
        
        Args:
            photo_id: Photo to comment on
            user_id: User creating the comment
            text: Comment text
            parent_comment_id: Parent comment for storage hierarchy
            reply_to_id: Specific comment being replied to (for UI context)
        """
        comment = Comment(
            photo_id=photo_id,
            user_id=user_id,
            text=text,
            parent_comment_id=parent_comment_id,
            reply_to_id=reply_to_id,
        )
        
        db.add(comment)
        db.commit()
        db.refresh(comment)
        
        # Update photo comment count
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if photo:
            photo.comment_count = db.query(Comment).filter(
                Comment.photo_id == photo_id,
                Comment.is_deleted == None  # is_deleted is DATETIME, NULL means not deleted
            ).count()
            db.commit()
        
        return comment
    
    @staticmethod
    def get_user_info(db: Session, user_id: str) -> dict:
        """Get user information for comment author."""
        # Check if user is a Studio
        studio = db.query(Studio).filter(Studio.id == user_id).first()
        if studio:
            return {
                "name": studio.studio_name,
                "avatar": studio.logo,
                "role": "studio",
            }
        
        # Check if user is a Client (via User table)
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            client = db.query(Client).filter(Client.user_id == user.id).first()
            if client:
                return {
                    "name": client.name,
                    "avatar": client.avatar,
                    "role": "client",
                }
        
        return {
            "name": "Unknown User",
            "avatar": None,
            "role": "unknown",
        }
    
    @staticmethod
    def build_comment_tree(
        db: Session,
        comments: List[Comment],
    ) -> List[dict]:
        """
        Build nested comment tree structure.
        
        Returns list of root comments with nested replies.
        """
        # Create lookup dictionaries
        comment_dict = {c.id: c for c in comments}
        comment_responses = {}
        
        # First pass: Create response objects with user info
        for comment in comments:
            user_info = CommentService.get_user_info(db, comment.user_id)
            
            # Get reply-to context if this is a reply
            reply_to_author = None
            reply_to_text = None
            if comment.reply_to_id and comment.reply_to_id in comment_dict:
                reply_to_comment = comment_dict[comment.reply_to_id]
                reply_to_info = CommentService.get_user_info(db, reply_to_comment.user_id)
                reply_to_author = reply_to_info["name"]
                reply_to_text = reply_to_comment.text[:50]  # First 50 chars
            
            comment_responses[comment.id] = {
                "id": comment.id,
                "photo_id": comment.photo_id,
                "user_id": comment.user_id,
                "text": comment.text,
                "author": "Studio" if user_info["role"] == "studio" else "Client",
                "user_name": user_info["name"],
                "user_avatar": user_info["avatar"],
                "parent_comment_id": comment.parent_comment_id,
                "reply_to_id": comment.reply_to_id,
                "reply_to_author": reply_to_author,
                "reply_to_text": reply_to_text,
                "is_edited": comment.is_edited,
                "timestamp": CommentService._format_timestamp(comment.created_at),
                "created_at": comment.created_at.isoformat(),
                "updated_at": comment.updated_at.isoformat(),
                "replies": [],
            }
        
        # Second pass: Build tree structure
        root_comments = []
        
        for comment_id, comment_data in comment_responses.items():
            parent_id = comment_data["parent_comment_id"]
            
            if parent_id is None:
                # Root comment
                root_comments.append(comment_data)
            elif parent_id in comment_responses:
                # Add to parent's replies
                comment_responses[parent_id]["replies"].append(comment_data)
        
        # Sort root comments by created_at (newest first)
        root_comments.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Sort replies within each comment (oldest first for conversation flow)
        def sort_replies(comment):
            comment["replies"].sort(key=lambda x: x["created_at"])
            for reply in comment["replies"]:
                sort_replies(reply)
        
        for comment in root_comments:
            sort_replies(comment)
        
        return root_comments
    
    @staticmethod
    def get_photo_comments(
        db: Session,
        photo_id: int,
    ) -> List[dict]:
        """Get all comments for a photo as nested tree."""
        comments = db.query(Comment).filter(
            Comment.photo_id == photo_id,
            Comment.is_deleted == None,  # is_deleted is DATETIME, NULL means not deleted
        ).all()
        
        return CommentService.build_comment_tree(db, comments)
    
    @staticmethod
    def update_comment(
        db: Session,
        comment_id: int,
        user_id: str,
        text: str,
    ) -> Comment:
        """Update a comment (only by original author)."""
        comment = db.query(Comment).filter(
            Comment.id == comment_id,
            Comment.user_id == user_id,
            Comment.is_deleted == None,  # is_deleted is DATETIME, NULL means not deleted
        ).first()
        
        if not comment:
            raise ValueError("Comment not found or unauthorized")
        
        comment.text = text
        comment.is_edited = True
        comment.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(comment)
        
        return comment
    
    @staticmethod
    def delete_comment(
        db: Session,
        comment_id: int,
        user_id: str,
    ) -> bool:
        """Soft delete a comment (only by original author)."""
        comment = db.query(Comment).filter(
            Comment.id == comment_id,
            Comment.user_id == user_id,
            Comment.is_deleted == None,  # is_deleted is DATETIME, NULL means not deleted
        ).first()
        
        if not comment:
            raise ValueError("Comment not found or unauthorized")
        
        comment.soft_delete()  # Use the soft_delete method from SoftDeleteMixin
        comment.updated_at = datetime.utcnow()
        
        # Update photo comment count
        photo = db.query(Photo).filter(Photo.id == comment.photo_id).first()
        if photo:
            photo.comment_count = db.query(Comment).filter(
                Comment.photo_id == comment.photo_id,
                Comment.is_deleted == None  # is_deleted is DATETIME, NULL means not deleted
            ).count()
        
        db.commit()
        
        return True
    
    @staticmethod
    def _format_timestamp(dt: datetime) -> str:
        """Format timestamp as human-readable string."""
        now = datetime.utcnow()
        diff = now - dt
        
        if diff.days > 365:
            return f"{diff.days // 365}y ago"
        elif diff.days > 30:
            return f"{diff.days // 30}mo ago"
        elif diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "just now"
