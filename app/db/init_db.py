"""Database initialisation and seed utilities."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path
from typing import Any, Iterable
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy.orm import Session

from app.core.config import get_settings

from . import engine, session_scope
from .base import Base
from . import models


def _namespace_uuid(value: str) -> str:
    """Derive a stable UUID5 string from any identifier."""

    return str(uuid5(NAMESPACE_URL, value))


def _resolve_id(legacy_id: str | None, seed: str) -> str:
    """Use legacy identifier when available, otherwise derive a stable UUID."""

    if legacy_id:
        legacy_id = str(legacy_id).strip()
        if legacy_id:
            return legacy_id
    return _namespace_uuid(seed)


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _parse_date(value: str | None) -> date | None:
    dt = _parse_datetime(value)
    return dt.date() if dt else None


def _load_json(file_name: str) -> list[dict[str, Any]]:
    settings = get_settings()
    path = Path(settings.data_directory) / file_name
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _first(iterable: Iterable[Any], default: Any = None) -> Any:
    for item in iterable:
        return item
    return default


def seed_database(session: Session) -> None:
    """Populate the SQLite database from the legacy JSON fixtures."""

    if session.query(models.Studio).first():
        return

    studios_raw = _load_json("studios.json")
    users_raw = _load_json("users.json")
    projects_raw = _load_json("projects.json")
    comments_raw = _load_json("comments.json")

    studio_id_map: dict[str, str] = {}
    user_id_map: dict[str, str] = {}
    client_key_map: dict[tuple[str, str], str] = {}
    project_id_map: dict[str, str] = {}
    category_id_map: dict[tuple[str, str], str] = {}
    image_id_map: dict[str, str] = {}
    tag_name_map: dict[str, str] = {}
    project_category_ids: defaultdict[str, list[str]] = defaultdict(list)

    studio_email_index: dict[str, str] = {}

    for studio in studios_raw:
        email = (studio.get("email") or f"{studio.get('id', 'studio')}@example.com").lower()
        legacy_id = (studio.get("id") or email).strip()

        if legacy_id in studio_id_map:
            continue

        if email in studio_email_index:
            existing_id = studio_email_index[email]
            studio_id_map[legacy_id] = existing_id
            continue

        studio_id = _resolve_id(legacy_id, f"studio:{email}")
        if studio_id in studio_email_index.values():
            studio_id = _namespace_uuid(f"studio:{email}:{legacy_id}")

        studio_obj = models.Studio(
            id=studio_id,
            name=studio.get("name") or studio.get("business_name") or email.split("@")[0].title(),
            business_name=studio.get("business_name"),
            email=email,
            phone=studio.get("phone"),
            website=studio.get("website"),
            address_line1=studio.get("address") or studio.get("address_line1"),
            address_line2=studio.get("address_line2"),
            city=studio.get("city"),
            state=studio.get("state"),
            postal_code=studio.get("postal_code"),
            country=studio.get("country"),
            logo_url=studio.get("logo_url"),
            brand_color=studio.get("brand_color"),
            subscription_tier="free",
            subscription_status="trial",
            max_projects=studio.get("max_projects", 5),
            max_storage_gb=studio.get("max_storage_gb", 10),
            storage_used_bytes=studio.get("storage_used_bytes", 0),
            is_active=studio.get("is_active", True),
            created_at=_parse_datetime(studio.get("created_at")) or datetime.utcnow(),
            updated_at=_parse_datetime(studio.get("updated_at")) or datetime.utcnow(),
        )
        session.add(studio_obj)
        studio_email_index[email] = studio_id
        studio_id_map[legacy_id] = studio_id
        studio_id_map[email] = studio_id

    session.flush()

    studio_owner_map: dict[str, str] = {}

    for user in users_raw:
        legacy_id = user.get("id")
        if legacy_id and legacy_id in user_id_map:
            continue

        email = (user.get("email") or f"{legacy_id}@example.com").lower()
        studio_ref = user.get("studio_id")
        studio_id = studio_id_map.get(studio_ref) if studio_ref else None
        role = user.get("role", "client")
        role_map = {
            "studio": "studio_owner",
            "studio_owner": "studio_owner",
            "studio_admin": "studio_admin",
            "studio_photographer": "studio_photographer",
            "client": "client",
        }
        mapped_role = role_map.get(role, "client")

        user_id = _resolve_id(legacy_id, f"user:{legacy_id}:{email}")
        user_obj = models.User(
            id=user_id,
            studio_id=studio_id,
            name=user.get("name") or email.split("@")[0].title(),
            email=email,
            password_hash=None,
            role=mapped_role,
            avatar_url=None,
            phone=user.get("phone"),
            last_login_at=_parse_datetime(user.get("last_login_at")),
            email_verified=user.get("email_verified", False),
            is_active=user.get("is_active", True),
            created_at=_parse_datetime(user.get("created_at")) or datetime.utcnow(),
            updated_at=_parse_datetime(user.get("updated_at")) or datetime.utcnow(),
        )
        session.add(user_obj)
        if legacy_id:
            user_id_map[legacy_id] = user_id
        else:
            user_id_map[email] = user_id

        if mapped_role == "studio_owner" and studio_id and studio_id not in studio_owner_map:
            studio_owner_map[studio_id] = user_id

    session.flush()

    client_seq_by_studio: defaultdict[str, int] = defaultdict(int)

    for project in projects_raw:
        legacy_project_id = project.get("id")
        studio_ref = project.get("studio_id")
        studio_id = studio_id_map.get(studio_ref) or _first(studio_id_map.values())
        if not studio_id:
            continue

        client_email = (project.get("client_email") or f"client-{legacy_project_id}@example.com").lower()
        client_key = (studio_id, client_email)
        if client_key not in client_key_map:
            client_seq_by_studio[studio_id] += 1
            client_id = _namespace_uuid(f"client:{studio_id}:{client_email}:{client_seq_by_studio[studio_id]}")
            client_obj = models.Client(
                id=client_id,
                studio_id=studio_id,
                user_id=None,
                name=project.get("client_name") or client_email.split("@")[0].title(),
                email=client_email,
                phone=None,
                secondary_email=None,
                address_line1=None,
                address_line2=None,
                city=None,
                state=None,
                postal_code=None,
                country=None,
                company_name=None,
                notes=None,
                status="active",
                total_projects=0,
                last_project_date=_parse_date(project.get("project_date")),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(client_obj)
            client_key_map[client_key] = client_id
        client_id = client_key_map[client_key]

        creator_id = studio_owner_map.get(studio_id) or _first(user_id_map.values())

        project_id = _resolve_id(legacy_project_id, f"project:{studio_id}:{client_email}")

        status_map = {
            "active": "review",
            "completed": "delivered",
            "draft": "draft",
        }

        project_status = status_map.get(project.get("status"), "draft")
        shoot_date = _parse_date(project.get("project_date"))

        project_obj = models.Project(
            id=project_id,
            studio_id=studio_id,
            client_id=client_id,
            created_by=creator_id,
            name=project.get("name") or "Untitled Project",
            description=project.get("description"),
            project_type=project.get("type") or project.get("project_type"),
            shoot_date=shoot_date,
            delivery_date=None,
            location=project.get("location"),
            access_url=project.get("access_url") or f"project-{project_id[:8]}",
            status=project_status,
            total_images=0,
            selected_images=0,
            total_comments=0,
            storage_used_bytes=0,
            last_viewed_at=None,
            view_count=0,
            created_at=_parse_datetime(project.get("created_at")) or datetime.utcnow(),
            updated_at=_parse_datetime(project.get("updated_at")) or datetime.utcnow(),
        )
        session.add(project_obj)
        if legacy_project_id:
            project_id_map[legacy_project_id] = project_id
        project_id_map[project_id] = project_id
        project_id_map[project_obj.access_url] = project_id

        settings_obj = models.ProjectSettings(
            id=_resolve_id(project.get("settings", {}).get("id"), f"project_settings:{project_id}"),
            project_id=project_id,
            is_password_protected=False,
            password_hash=None,
            allow_downloads=True,
            allow_comments=True,
            allow_selections=True,
            allow_favorites=True,
            watermark_enabled=True,
            watermark_text=None,
            max_selections=None,
            expires_at=None,
            auto_archive_days=90,
            notification_email=None,
            custom_message=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(settings_obj)

        category_counts: defaultdict[str, int] = defaultdict(int)
        project_total_comments = 0
        project_total_images = 0
        project_selected_images = 0
        project_storage_bytes = 0

        for category in project.get("categories", []):
            legacy_category_id = category.get("id") or f"category-{legacy_project_id}-{category.get('name')}"
            category_id = _namespace_uuid(f"category:{legacy_category_id}:{project_id}")
            category_obj = models.Category(
                id=category_id,
                project_id=project_id,
                name=category.get("name") or "category",
                display_name=category.get("display_name") or category.get("name") or "Category",
                description=category.get("description"),
                cover_image_id=None,
                order_index=category.get("order", category.get("order_index", 0)),
                is_default=category.get("is_default", False),
                image_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(category_obj)
            category_id_map[(legacy_project_id, legacy_category_id)] = category_id
            project_category_ids[project_id].append(category_id)

        for image in project.get("images", []):
            legacy_image_id = image.get("id")
            category_ref = image.get("category_id")
            category_id = category_id_map.get((legacy_project_id, category_ref))
            if not category_id:
                category_id = _first(project_category_ids.get(project_id, []))
            if not category_id:
                continue

            image_id = _namespace_uuid(f"image:{legacy_image_id}:{project_id}")
            version = _first(image.get("versions", []), default={})
            url = version.get("url") or ""
            thumbnail = version.get("thumbnail")
            file_size = int(version.get("file_size") or image.get("file_size", 0) or 0)
            metadata = image.get("metadata", {})

            is_favorite = image.get("is_favorite", False)
            is_selected = image.get("is_selected", False)

            capture_dt = _parse_datetime(metadata.get("captured_at"))

            image_obj = models.Image(
                id=image_id,
                project_id=project_id,
                category_id=category_id,
                uploaded_by=creator_id,
                original_filename=image.get("original_file_name") or version.get("file_name") or "photo.jpg",
                s3_key_original=url,
                s3_key_thumbnail=thumbnail,
                s3_key_preview=None,
                s3_key_print=None,
                file_size_bytes=file_size,
                mime_type="image/jpeg",
                width=metadata.get("width"),
                height=metadata.get("height"),
                captured_at=capture_dt,
                camera_make=metadata.get("camera"),
                camera_model=metadata.get("camera"),
                iso=None,
                f_stop=None,
                shutter_speed=None,
                focal_length=metadata.get("lens"),
                gps_latitude=None,
                gps_longitude=None,
                rating=0,
                is_favorite=is_favorite,
                is_selected=is_selected,
                status="ready",
                uploaded_at=_parse_datetime(version.get("uploaded_at")) or datetime.utcnow(),
                updated_at=_parse_datetime(image.get("updated_at")) or datetime.utcnow(),
            )
            session.add(image_obj)
            image_id_map[legacy_image_id] = image_id

            if version:
                version_obj = models.ImageVersion(
                    id=_namespace_uuid(f"image_version:{version.get('id', legacy_image_id)}:{image_id}"),
                    image_id=image_id,
                    version_name=version.get("version") or "original",
                    s3_key=url,
                    file_size_bytes=file_size or None,
                    width=metadata.get("width"),
                    height=metadata.get("height"),
                    created_by=creator_id,
                    created_at=_parse_datetime(version.get("uploaded_at")) or datetime.utcnow(),
                )
                session.add(version_obj)

            for tag_name in image.get("tags", []) or []:
                tag_key = tag_name.lower().strip()
                if not tag_key:
                    continue
                if tag_key not in tag_name_map:
                    tag_obj = models.Tag(
                        id=_namespace_uuid(f"tag:{tag_key}"),
                        studio_id=studio_id,
                        name=tag_key,
                        color=None,
                        created_at=datetime.utcnow(),
                    )
                    session.add(tag_obj)
                    tag_name_map[tag_key] = tag_obj.id
                image_tag = models.ImageTag(image_id=image_id, tag_id=tag_name_map[tag_key])
                session.add(image_tag)

            category_counts[category_id] += 1
            project_total_images += 1
            project_storage_bytes += file_size
            if is_selected:
                project_selected_images += 1
            project_total_comments += int(image.get("comment_count", 0) or 0)

        for category in session.query(models.Category).filter(models.Category.project_id == project_id):
            category.image_count = category_counts.get(category.id, 0)

        project_obj.total_images = project_total_images
        project_obj.selected_images = project_selected_images
        project_obj.storage_used_bytes = project_storage_bytes
        project_obj.total_comments = project_total_comments

    session.flush()

    project_comment_totals: defaultdict[str, int] = defaultdict(int)
    image_comment_totals: defaultdict[str, int] = defaultdict(int)

    pending_comments: list[tuple[str | None, models.Comment]] = []

    for comment in comments_raw:
        image_ref = comment.get("image_id")
        project_ref = comment.get("project_id")
        user_ref = comment.get("user_id")

        image_id = image_id_map.get(image_ref)
        project_id = project_id_map.get(project_ref)
        user_id = user_id_map.get(user_ref)

        if not image_id or not project_id or not user_id:
            continue

        comment_id = _namespace_uuid(f"comment:{comment.get('id')}")
        parent_ref = comment.get("parent_id")
        parent_id = _namespace_uuid(f"comment:{parent_ref}") if parent_ref else None

        comment_obj = models.Comment(
            id=comment_id,
            image_id=image_id,
            user_id=user_id,
            parent_id=parent_id,
            content=comment.get("content") or "",
            resolved=comment.get("resolved", False),
            created_at=_parse_datetime(comment.get("created_at")) or datetime.utcnow(),
            updated_at=_parse_datetime(comment.get("updated_at")) or datetime.utcnow(),
        )
        pending_comments.append((parent_id, comment_obj))

        image_comment_totals[image_id] += 1
        project_comment_totals[project_id] += 1

    inserted_comments: set[str] = set()
    while pending_comments:
        remaining: list[tuple[str | None, models.Comment]] = []
        progress = False

        for parent_id, comment_obj in pending_comments:
            if parent_id and parent_id not in inserted_comments:
                remaining.append((parent_id, comment_obj))
                continue
            session.add(comment_obj)
            inserted_comments.add(comment_obj.id)
            progress = True

        if not progress:
            for _, comment_obj in remaining:
                comment_obj.parent_id = None
                session.add(comment_obj)
                inserted_comments.add(comment_obj.id)
            break

        pending_comments = remaining

    for image in session.query(models.Image):
        image.comment_count = image_comment_totals.get(image.id, 0)

    for project in session.query(models.Project):
        project.total_comments = project_comment_totals.get(project.id, 0)

    for client in session.query(models.Client):
        client_projects = session.query(models.Project).filter(models.Project.client_id == client.id).all()
        client.total_projects = len(client_projects)
        client.last_project_date = _first(
            sorted((p.shoot_date for p in client_projects if p.shoot_date), reverse=True)
        )
        client.updated_at = datetime.utcnow()

    session.flush()


def init_db() -> None:
    """Create tables and seed data if required."""

    Base.metadata.create_all(bind=engine)
    with session_scope() as session:
        seed_database(session)
