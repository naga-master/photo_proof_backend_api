"""Studio management and tenant endpoints."""

import base64
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.db.models import Studio, StudioDomain, SubscriptionPlan, StudioSubscription, StudioFeature
from app.api.deps import get_current_studio, get_optional_studio, require_studio_user
from app.core.dependencies import get_current_user
from app.schemas import UserRead
from app.services.storage_service import tenant_storage
from app.services.cache_service import cache_studio_theme, get_cached_studio_theme, invalidate_studio_cache
from app.core.config import get_settings
from pydantic import BaseModel


def save_branding_image_from_base64(studio_id: str, base64_data: str, image_type: str) -> str:
    """
    Save base64 image to file system and return the URL path.
    
    Args:
        studio_id: The studio's ID
        base64_data: Base64 encoded image (data:image/png;base64,...)
        image_type: Type of image ('logo', 'studio_photo', 'display_image')
    
    Returns:
        URL path to the saved image
    """
    settings = get_settings()
    
    if not base64_data.startswith('data:image'):
        raise ValueError("Invalid image data format")
    
    header, encoded = base64_data.split(',', 1)
    mime_type = header.split(':')[1].split(';')[0]
    ext_map = {
        'image/jpeg': 'jpg',
        'image/jpg': 'jpg',
        'image/png': 'png',
        'image/gif': 'gif',
        'image/webp': 'webp',
        'image/svg+xml': 'svg',
    }
    extension = ext_map.get(mime_type, 'png')
    
    studio_dir = Path(settings.uploads_directory) / 'studios' / studio_id
    studio_dir.mkdir(parents=True, exist_ok=True)
    
    # Use consistent filename based on image type
    filename = f"{image_type}.{extension}"
    filepath = studio_dir / filename
    
    image_data = base64.b64decode(encoded)
    with open(filepath, 'wb') as f:
        f.write(image_data)
    
    return f"/uploads/studios/{studio_id}/{filename}"


router = APIRouter(prefix="/studio", tags=["Studio"])


# ========== Response Models ==========

class StudioThemeResponse(BaseModel):
    """Studio theme/branding information for frontend."""
    id: str
    name: str
    subdomain: Optional[str]
    logo_url: Optional[str]
    brand_color: str
    typography: str
    custom_css: Optional[str]
    studio_photo: Optional[str] = None
    studio_description: Optional[str] = None
    
    class Config:
        from_attributes = True


class StorageStatsResponse(BaseModel):
    """Storage usage statistics."""
    total_bytes: int
    total_mb: float
    total_gb: float
    photo_count: int
    logo_count: int
    other_count: int
    max_storage_gb: int
    usage_percentage: float


class SubscriptionResponse(BaseModel):
    """Subscription information."""
    plan_name: str
    plan_display_name: str
    status: str
    trial_ends_at: Optional[str]
    current_period_end: str
    max_projects: int
    max_storage_gb: int
    max_users: int
    features: dict


class StudioDetailsResponse(BaseModel):
    """Complete studio information."""
    id: str
    name: str
    email: str
    subdomain: Optional[str]
    brand_color: str
    logo_url: Optional[str]
    onboarding_completed: bool
    subscription: Optional[SubscriptionResponse]
    storage: StorageStatsResponse
    domains: list[str]


class StudioBrandingUpdate(BaseModel):
    """Request model for updating studio branding."""
    logo_url: Optional[str] = None
    brand_color: Optional[str] = None
    typography: Optional[str] = None
    custom_css: Optional[str] = None
    name: Optional[str] = None
    studio_photo: Optional[str] = None  # Base64 or URL for About page photo
    studio_description: Optional[str] = None  # About page description


# ========== Endpoints ==========

@router.get("/current", response_model=StudioThemeResponse)
async def get_current_studio_theme(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get current studio's theme/branding information.
    
    This endpoint is called by the frontend to load studio-specific branding.
    Uses domain from Host header to determine which studio.
    
    **Caching:** Theme is cached for 30 minutes for performance.
    """
    studio = get_optional_studio(request)
    
    if not studio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No studio found for this domain. Please access via a valid studio domain."
        )
    
    # Check cache first
    cached_theme = get_cached_studio_theme(studio.id)
    if cached_theme:
        return cached_theme
    
    # Build theme response
    theme = StudioThemeResponse(
        id=studio.id,
        name=studio.name,
        subdomain=studio.subdomain,
        logo_url=studio.logo_url,
        brand_color=studio.brand_color,
        typography=studio.typography,
        custom_css=studio.custom_css,
        studio_photo=studio.studio_photo,
        studio_description=studio.studio_description
    )
    
    # Cache for 30 minutes
    cache_studio_theme(studio.id, theme.dict(), ttl=1800)
    
    return theme


@router.get("/details", response_model=StudioDetailsResponse)
async def get_studio_details(
    studio: Studio = Depends(get_current_studio),
    db: Session = Depends(get_db)
):
    """Get complete studio information including subscription and storage stats.
    
    Requires authentication as studio user.
    """
    # Get subscription
    subscription_data = None
    if studio.subscription:
        sub = studio.subscription
        subscription_data = SubscriptionResponse(
            plan_name=sub.plan.name,
            plan_display_name=sub.plan.display_name,
            status=sub.status,
            trial_ends_at=sub.trial_ends_at.isoformat() if sub.trial_ends_at else None,
            current_period_end=sub.current_period_end.isoformat(),
            max_projects=sub.plan.max_projects,
            max_storage_gb=sub.plan.max_storage_gb,
            max_users=sub.plan.max_users,
            features=sub.plan.features or {}
        )
    
    # Get storage stats
    storage_stats = tenant_storage.get_storage_stats(studio.id)
    storage_stats["max_storage_gb"] = studio.max_storage_gb
    max_bytes = studio.max_storage_gb * 1024 * 1024 * 1024
    storage_stats["usage_percentage"] = (storage_stats["total_bytes"] / max_bytes * 100) if max_bytes > 0 else 0
    
    # Get domains
    domains = [d.domain for d in studio.domains]
    
    return StudioDetailsResponse(
        id=studio.id,
        name=studio.name,
        email=studio.email,
        subdomain=studio.subdomain,
        brand_color=studio.brand_color,
        logo_url=studio.logo_url,
        onboarding_completed=studio.onboarding_completed,
        subscription=subscription_data,
        storage=StorageStatsResponse(**storage_stats),
        domains=domains
    )


@router.get("/storage/stats", response_model=StorageStatsResponse)
async def get_storage_stats(
    studio: Studio = Depends(get_current_studio)
):
    """Get storage usage statistics for current studio."""
    stats = tenant_storage.get_storage_stats(studio.id)
    stats["max_storage_gb"] = studio.max_storage_gb
    
    # Calculate usage percentage
    max_bytes = studio.max_storage_gb * 1024 * 1024 * 1024
    stats["usage_percentage"] = (stats["total_bytes"] / max_bytes * 100) if max_bytes > 0 else 0
    
    return StorageStatsResponse(**stats)


@router.get("/subscription")
async def get_subscription_info(
    studio: Studio = Depends(get_current_studio),
    db: Session = Depends(get_db)
):
    """Get current subscription information."""
    if not studio.subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    sub = studio.subscription
    
    return {
        "id": sub.id,
        "plan": {
            "name": sub.plan.name,
            "display_name": sub.plan.display_name,
            "price_monthly": float(sub.plan.price_monthly),
            "features": sub.plan.features
        },
        "status": sub.status,
        "trial_ends_at": sub.trial_ends_at.isoformat() if sub.trial_ends_at else None,
        "current_period_start": sub.current_period_start.isoformat(),
        "current_period_end": sub.current_period_end.isoformat(),
        "cancel_at_period_end": sub.cancel_at_period_end
    }


@router.get("/plans")
async def list_subscription_plans(
    db: Session = Depends(get_db)
):
    """List all available subscription plans.
    
    Public endpoint - no authentication required.
    """
    plans = db.query(SubscriptionPlan).filter_by(
        is_active=True,
        is_visible=True
    ).order_by(SubscriptionPlan.sort_order).all()
    
    return [
        {
            "id": plan.id,
            "name": plan.name,
            "display_name": plan.display_name,
            "description": plan.description,
            "price_monthly": float(plan.price_monthly),
            "price_yearly": float(plan.price_yearly) if plan.price_yearly else None,
            "max_projects": plan.max_projects,
            "max_storage_gb": plan.max_storage_gb,
            "max_users": plan.max_users,
            "features": plan.features or {}
        }
        for plan in plans
    ]


@router.post("/theme/invalidate-cache")
async def invalidate_theme_cache(
    studio: Studio = Depends(get_current_studio)
):
    """Invalidate cached theme for current studio.
    
    Call this after updating studio branding to refresh the cache.
    """
    invalidate_studio_cache(studio.id)
    
    return {
        "message": "Theme cache invalidated successfully",
        "studio_id": studio.id
    }


@router.patch("/branding")
async def update_studio_branding(
    data: StudioBrandingUpdate,
    request_studio: Studio = Depends(get_current_studio),
    db: Session = Depends(get_db)
):
    """Update studio branding (logo, colors, typography, etc.).
    
    Only updates fields that are provided (non-null).
    Automatically invalidates the theme cache after update.
    Supports base64 encoded images for logo and studio_photo.
    
    **Fields:**
    - `logo_url`: URL or base64 data for studio logo
    - `brand_color`: Hex color code (e.g., "#1e293b")
    - `typography`: Font/typography preference
    - `custom_css`: Custom CSS overrides
    - `name`: Studio display name
    - `studio_photo`: URL or base64 data for About page photo
    - `studio_description`: About page description text
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # IMPORTANT: The studio from get_current_studio is DETACHED from the session
    # (the tenant middleware closes its session). We need to get a fresh copy.
    studio = db.query(Studio).filter(Studio.id == request_studio.id).first()
    if not studio:
        raise HTTPException(status_code=404, detail="Studio not found")
    
    logger.info(f"Updating branding for studio: {studio.id} ({studio.name})")
    
    # Update only provided fields
    if data.logo_url is not None:
        if data.logo_url.startswith('data:image'):
            try:
                studio.logo_url = save_branding_image_from_base64(studio.id, data.logo_url, 'logo')
            except Exception as e:
                logger.error(f"Failed to save logo: {e}")
        else:
            studio.logo_url = data.logo_url
            
    if data.brand_color is not None:
        studio.brand_color = data.brand_color
    if data.typography is not None:
        studio.typography = data.typography
    if data.custom_css is not None:
        studio.custom_css = data.custom_css
    if data.name is not None:
        studio.name = data.name
        
    # Handle studio photo (About page image)
    if data.studio_photo is not None:
        logger.info(f"Processing studio_photo for studio {studio.id}, is_base64: {data.studio_photo.startswith('data:image')}")
        if data.studio_photo.startswith('data:image'):
            try:
                photo_url = save_branding_image_from_base64(studio.id, data.studio_photo, 'studio_photo')
                studio.studio_photo = photo_url
                logger.info(f"Saved studio photo to: {photo_url}")
            except Exception as e:
                logger.error(f"Failed to save studio photo: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Failed to save studio photo: {str(e)}")
        else:
            studio.studio_photo = data.studio_photo
            logger.info(f"Set studio photo URL directly: {data.studio_photo}")
            
    # Handle studio description
    if data.studio_description is not None:
        studio.studio_description = data.studio_description
        logger.info(f"Set studio description: {data.studio_description[:50]}...")
    
    # Log what we're about to save
    logger.info(f"About to commit studio update: studio_photo={studio.studio_photo}, studio_description={studio.studio_description is not None}")
    
    db.commit()
    db.refresh(studio)  # Ensure we have the latest from DB
    
    logger.info(f"After commit: studio_photo={studio.studio_photo}, studio_description={studio.studio_description is not None}")
    
    # Invalidate cache so changes are reflected immediately
    invalidate_studio_cache(studio.id)
    
    return {
        "message": "Branding updated successfully",
        "studio_id": studio.id,
        "updated_fields": [
            field for field, value in data.model_dump().items() 
            if value is not None
        ]
    }


@router.get("/features")
async def get_studio_features(
    studio: Studio = Depends(get_current_studio),
    db: Session = Depends(get_db)
):
    """Get enabled features for current studio.
    
    Features can come from:
    1. Subscription plan features (base features)
    2. Studio-specific feature overrides
    """
    # Get plan features
    plan_features = {}
    if studio.subscription and studio.subscription.plan.features:
        plan_features = studio.subscription.plan.features
    
    # Get studio feature overrides
    studio_features = db.query(StudioFeature).filter_by(
        studio_id=studio.id,
        enabled=True
    ).all()
    
    # Merge features (studio overrides take precedence)
    features = {**plan_features}
    for feature in studio_features:
        features[feature.feature_key] = feature.config or True
    
    return {
        "studio_id": studio.id,
        "features": features,
        "subscription_plan": studio.subscription.plan.name if studio.subscription else None
    }


@router.get("/domains")
async def list_studio_domains(
    studio: Studio = Depends(get_current_studio),
    db: Session = Depends(get_db)
):
    """List all domains configured for current studio."""
    domains = db.query(StudioDomain).filter_by(studio_id=studio.id).all()
    
    return [
        {
            "id": d.id,
            "domain": d.domain,
            "subdomain": d.subdomain,
            "is_primary": d.is_primary,
            "is_verified": d.is_verified,
            "verified_at": d.verified_at.isoformat() if d.verified_at else None
        }
        for d in domains
    ]


class DashboardMetricsResponse(BaseModel):
    """Dashboard metrics response with delta comparisons."""
    total_projects: int
    total_photos: int
    total_comments: int
    active_clients: int
    # Delta fields (change from last month)
    projects_delta: int
    photos_delta: int
    comments_delta: int
    clients_delta: int


@router.get("/dashboard-metrics", response_model=DashboardMetricsResponse)
async def get_dashboard_metrics(
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard metrics with accurate counts and month-over-month deltas.
    
    Calculates metrics dynamically to avoid stale cached counts.
    Uses the user's studio_id from JWT token for multi-tenant filtering.
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func, distinct, and_
    from app.db.models import Project, Photo, Client, Comment
    
    studio_id = current_user.studio_id
    one_month_ago = datetime.utcnow() - timedelta(days=30)
    
    # Current counts
    total_projects = db.query(func.count(Project.id)).filter(
        Project.studio_id == studio_id
    ).scalar() or 0
    
    total_photos = db.query(func.count(Photo.id)).join(
        Project, Photo.project_id == Project.id
    ).filter(
        Project.studio_id == studio_id,
        Photo.status == "completed"
    ).scalar() or 0
    
    total_comments = db.query(func.count(Comment.id)).join(
        Photo, Comment.photo_id == Photo.id
    ).join(
        Project, Photo.project_id == Project.id
    ).filter(
        Project.studio_id == studio_id
    ).scalar() or 0
    
    active_clients = db.query(func.count(distinct(Project.client_id))).filter(
        Project.studio_id == studio_id
    ).scalar() or 0
    
    # Counts from 30 days ago (items that existed before that date)
    projects_last_month = db.query(func.count(Project.id)).filter(
        Project.studio_id == studio_id,
        Project.created_at < one_month_ago
    ).scalar() or 0
    
    photos_last_month = db.query(func.count(Photo.id)).join(
        Project, Photo.project_id == Project.id
    ).filter(
        Project.studio_id == studio_id,
        Photo.status == "completed",
        Photo.created_at < one_month_ago
    ).scalar() or 0
    
    comments_last_month = db.query(func.count(Comment.id)).join(
        Photo, Comment.photo_id == Photo.id
    ).join(
        Project, Photo.project_id == Project.id
    ).filter(
        Project.studio_id == studio_id,
        Comment.created_at < one_month_ago
    ).scalar() or 0
    
    clients_last_month = db.query(func.count(distinct(Project.client_id))).filter(
        Project.studio_id == studio_id,
        Project.created_at < one_month_ago
    ).scalar() or 0
    
    return DashboardMetricsResponse(
        total_projects=total_projects,
        total_photos=total_photos,
        total_comments=total_comments,
        active_clients=active_clients,
        projects_delta=total_projects - projects_last_month,
        photos_delta=total_photos - photos_last_month,
        comments_delta=total_comments - comments_last_month,
        clients_delta=active_clients - clients_last_month
    )
