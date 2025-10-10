"""SQLAlchemy ORM models for the Photo Proof application."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _uuid() -> str:
    """Generate a new UUID4 string."""

    return str(uuid.uuid4())


SubscriptionTier = Enum("free", "basic", "professional", "enterprise", name="subscription_tier_enum")
SubscriptionStatus = Enum("active", "trial", "cancelled", "suspended", name="subscription_status_enum")
UserRole = Enum(
    "studio_owner",
    "studio_admin",
    "studio_photographer",
    "client",
    name="user_role_enum",
)
ClientStatus = Enum("active", "inactive", "archived", name="client_status_enum")
ProjectStatus = Enum(
    "draft",
    "uploading",
    "processing",
    "review",
    "delivered",
    "archived",
    name="project_status_enum",
)
ImageStatus = Enum(
    "uploaded",
    "processing",
    "ready",
    "archived",
    "deleted",
    name="image_status_enum",
)


class Studio(Base):
    __tablename__ = "studios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), index=True)
    business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    brand_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    subscription_tier: Mapped[str] = mapped_column(SubscriptionTier, default="free")
    subscription_status: Mapped[str] = mapped_column(SubscriptionStatus, default="trial")
    max_projects: Mapped[int] = mapped_column(Integer, default=5)
    max_storage_gb: Mapped[int] = mapped_column(Integer, default=10)
    storage_used_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users: Mapped[list["User"]] = relationship("User", back_populates="studio", cascade="all, delete-orphan")
    clients: Mapped[list["Client"]] = relationship("Client", back_populates="studio", cascade="all, delete-orphan")
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="studio", cascade="all, delete-orphan")
    tags: Mapped[list["Tag"]] = relationship("Tag", back_populates="studio", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    studio_id: Mapped[str | None] = mapped_column(ForeignKey("studios.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(UserRole, nullable=False, index=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    studio: Mapped[Studio | None] = relationship("Studio", back_populates="users")
    uploaded_images: Mapped[list["Image"]] = relationship("Image", back_populates="uploader")
    selections: Mapped[list["ImageSelection"]] = relationship("ImageSelection", back_populates="user", cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="user", cascade="all, delete-orphan")


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    studio_id: Mapped[str] = mapped_column(ForeignKey("studios.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    secondary_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(ClientStatus, default="active", index=True)
    total_projects: Mapped[int] = mapped_column(Integer, default=0)
    last_project_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    studio: Mapped[Studio] = relationship("Studio", back_populates="clients")
    user: Mapped[User | None] = relationship("User")
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="client", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("studio_id", "email", name="uq_clients_studio_email"),)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    studio_id: Mapped[str] = mapped_column(ForeignKey("studios.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    shoot_date: Mapped[Date | None] = mapped_column(Date, nullable=True, index=True)
    delivery_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    access_url: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(ProjectStatus, default="draft", index=True)
    total_images: Mapped[int] = mapped_column(Integer, default=0)
    selected_images: Mapped[int] = mapped_column(Integer, default=0)
    total_comments: Mapped[int] = mapped_column(Integer, default=0)
    storage_used_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    last_viewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    studio: Mapped[Studio] = relationship("Studio", back_populates="projects")
    client: Mapped[Client] = relationship("Client", back_populates="projects")
    creator: Mapped[User] = relationship("User")
    settings: Mapped[ProjectSettings | None] = relationship(
        "ProjectSettings",
        back_populates="project",
        cascade="all, delete-orphan",
        uselist=False,
    )
    categories: Mapped[list["Category"]] = relationship("Category", back_populates="project", cascade="all, delete-orphan")
    images: Mapped[list["Image"]] = relationship("Image", back_populates="project", cascade="all, delete-orphan")


class ProjectSettings(Base):
    __tablename__ = "project_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), unique=True, nullable=False)
    is_password_protected: Mapped[bool] = mapped_column(Boolean, default=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    allow_downloads: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_comments: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_selections: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_favorites: Mapped[bool] = mapped_column(Boolean, default=True)
    watermark_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    watermark_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    max_selections: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    auto_archive_days: Mapped[int] = mapped_column(Integer, default=90)
    notification_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    custom_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project: Mapped[Project] = relationship("Project", back_populates="settings")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_image_id: Mapped[str | None] = mapped_column(ForeignKey("images.id", ondelete="SET NULL"), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    image_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project: Mapped[Project] = relationship("Project", back_populates="categories")
    images: Mapped[list["Image"]] = relationship("Image", back_populates="category", foreign_keys="Image.category_id")
    cover_image: Mapped[Image | None] = relationship("Image", foreign_keys=[cover_image_id], post_update=True)

    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_categories_project_name"),)


class Image(Base):
    __tablename__ = "images"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id: Mapped[str] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    s3_key_original: Mapped[str] = mapped_column(Text, nullable=False)
    s3_key_thumbnail: Mapped[str | None] = mapped_column(Text, nullable=True)
    s3_key_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    s3_key_print: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    camera_make: Mapped[str | None] = mapped_column(String(100), nullable=True)
    camera_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    iso: Mapped[int | None] = mapped_column(Integer, nullable=True)
    f_stop: Mapped[Numeric | None] = mapped_column(Numeric(4, 2), nullable=True)
    shutter_speed: Mapped[str | None] = mapped_column(String(50), nullable=True)
    focal_length: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gps_latitude: Mapped[Numeric | None] = mapped_column(Numeric(10, 8), nullable=True)
    gps_longitude: Mapped[Numeric | None] = mapped_column(Numeric(11, 8), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, default=0)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(ImageStatus, default="uploaded", index=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project: Mapped[Project] = relationship("Project", back_populates="images")
    category: Mapped[Category] = relationship("Category", back_populates="images", foreign_keys=[category_id])
    uploader: Mapped[User] = relationship("User", back_populates="uploaded_images")
    versions: Mapped[list["ImageVersion"]] = relationship("ImageVersion", back_populates="image", cascade="all, delete-orphan")
    selections: Mapped[list["ImageSelection"]] = relationship("ImageSelection", back_populates="image", cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="image", cascade="all, delete-orphan")
    tags: Mapped[list["Tag"]] = relationship("Tag", secondary="image_tags", back_populates="images")


class ImageVersion(Base):
    __tablename__ = "image_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    image_id: Mapped[str] = mapped_column(ForeignKey("images.id", ondelete="CASCADE"), nullable=False, index=True)
    version_name: Mapped[str] = mapped_column(String(100), nullable=False)
    s3_key: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    image: Mapped[Image] = relationship("Image", back_populates="versions")
    creator: Mapped[User | None] = relationship("User")

    __table_args__ = (UniqueConstraint("image_id", "version_name", name="uq_image_versions_name"),)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    studio_id: Mapped[str | None] = mapped_column(ForeignKey("studios.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    studio: Mapped[Studio | None] = relationship("Studio", back_populates="tags")
    images: Mapped[list[Image]] = relationship("Image", secondary="image_tags", back_populates="tags")


class ImageTag(Base):
    __tablename__ = "image_tags"

    image_id: Mapped[str] = mapped_column(ForeignKey("images.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[str] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)


class ImageSelection(Base):
    __tablename__ = "image_selections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    image_id: Mapped[str] = mapped_column(ForeignKey("images.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    selected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    image: Mapped[Image] = relationship("Image", back_populates="selections")
    user: Mapped[User] = relationship("User", back_populates="selections")

    __table_args__ = (UniqueConstraint("image_id", "user_id", name="uq_image_selections_image_user"),)


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    image_id: Mapped[str] = mapped_column(ForeignKey("images.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    image: Mapped[Image] = relationship("Image", back_populates="comments")
    user: Mapped[User] = relationship("User", back_populates="comments")
    parent: Mapped[Comment | None] = relationship("Comment", remote_side="Comment.id", back_populates="replies")
    replies: Mapped[list["Comment"]] = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")
