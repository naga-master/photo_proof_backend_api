"""Photo, Comment, and user interaction models."""

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base, TimestampMixin, SoftDeleteMixin


class Photo(Base, TimestampMixin):
    """Photo/Image entity."""

    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    folder_id = Column(String(36), ForeignKey("folders.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # File info
    src = Column(String(1000), nullable=False)  # URL or path to photo
    alt = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    storage_path = Column(String(1000), nullable=False)  # Local path or S3 key
    thumbnail_path = Column(String(1000), nullable=True)
    preview_path = Column(String(1000), nullable=True)
    
    # Dimensions and metadata
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    mime_type = Column(String(100), nullable=False, default='image/jpeg')
    
    # EXIF data
    captured_at = Column(DateTime, nullable=True)
    camera = Column(String(255), nullable=True)
    lens = Column(String(255), nullable=True)
    
    # Ordering
    order_index = Column(Integer, nullable=False, default=0)
    
    # Cached count
    comment_count = Column(Integer, nullable=False, default=0)
    
    # Upload info
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    status = Column(String(50), nullable=False, default='completed')
    # Statuses: 'pending', 'uploading', 'completed', 'failed'

    # Relationships
    project = relationship("Project", back_populates="photos", foreign_keys=[project_id])
    folder = relationship("Folder", back_populates="photos", foreign_keys=[folder_id])
    uploaded_by_user = relationship("User", back_populates="uploaded_photos", foreign_keys=[uploaded_by])
    comments = relationship("Comment", back_populates="photo", cascade="all, delete-orphan", foreign_keys="Comment.photo_id")
    favorites = relationship("UserPhotoFavorite", back_populates="photo", cascade="all, delete-orphan")
    selections = relationship("UserPhotoSelection", back_populates="photo", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="photo")

    def __repr__(self):
        return f"<Photo(id={self.id}, filename={self.original_filename})>"


class Comment(Base, TimestampMixin, SoftDeleteMixin):
    """Comment on a photo with support for nested replies.
    
    Structure:
    - Top-level comments: parent_comment_id = None
    - Replies: parent_comment_id = top-level comment id (always attach to root)
    - reply_to_id: tracks which specific message was replied to (for display context)
    
    Example:
      Comment 1 (parent=None)                    <- Top level
        ├─ Reply 2 (parent=1, reply_to=1)       <- Reply to Comment 1
        └─ Reply 3 (parent=1, reply_to=2)       <- Reply to Reply 2, but stored under Comment 1
    """

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    photo_id = Column(Integer, ForeignKey("photos.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Text content
    text = Column(Text, nullable=False)  # Max 1000 chars enforced in application layer
    
    # Nested reply structure
    parent_comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)
    # CRITICAL: reply_to_id tracks which specific message was replied to (for WhatsApp-style context)
    reply_to_id = Column(Integer, ForeignKey("comments.id", ondelete="SET NULL"), nullable=True)
    
    # Metadata
    is_edited = Column(Boolean, nullable=False, default=False)
    timestamp = Column(String(100), nullable=True)  # Human-readable: "Just now", "2 days ago"

    # Relationships
    photo = relationship("Photo", back_populates="comments", foreign_keys=[photo_id])
    user = relationship("User", back_populates="comments", foreign_keys=[user_id])
    
    # Self-referential for nested structure
    parent_comment = relationship(
        "Comment", 
        remote_side=[id], 
        backref="replies", 
        foreign_keys=[parent_comment_id]
    )
    
    # For reply context
    reply_to = relationship("Comment", remote_side=[id], foreign_keys=[reply_to_id], post_update=True)

    @property
    def author(self):
        """Computed author type from user role."""
        if self.user.role in ['studio_owner', 'studio_admin', 'studio_photographer']:
            return 'Studio'
        return 'Client'

    def __repr__(self):
        return f"<Comment(id={self.id}, photo_id={self.photo_id}, user={self.user.name})>"


class UserPhotoFavorite(Base, TimestampMixin):
    """Junction table for user's favorite photos."""

    __tablename__ = "user_photo_favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    photo_id = Column(Integer, ForeignKey("photos.id", ondelete="CASCADE"), nullable=False, index=True)

    # Ensure unique user-photo combination
    __table_args__ = (
        UniqueConstraint('user_id', 'photo_id', name='uq_user_photo_favorite'),
    )

    # Relationships
    user = relationship("User", back_populates="favorites")
    photo = relationship("Photo", back_populates="favorites")

    def __repr__(self):
        return f"<UserPhotoFavorite(user_id={self.user_id}, photo_id={self.photo_id})>"


class UserPhotoSelection(Base, TimestampMixin):
    """Junction table for user's selected photos (for purchase/final picks)."""

    __tablename__ = "user_photo_selections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    photo_id = Column(Integer, ForeignKey("photos.id", ondelete="CASCADE"), nullable=False, index=True)

    # Ensure unique user-photo combination
    __table_args__ = (
        UniqueConstraint('user_id', 'photo_id', name='uq_user_photo_selection'),
    )

    # Relationships
    user = relationship("User", back_populates="selections")
    photo = relationship("Photo", back_populates="selections")

    def __repr__(self):
        return f"<UserPhotoSelection(user_id={self.user_id}, photo_id={self.photo_id})>"
