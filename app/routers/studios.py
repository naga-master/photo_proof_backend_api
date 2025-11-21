"""Studio management and tenant endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.db.models import Studio, StudioDomain, SubscriptionPlan, StudioSubscription, StudioFeature
from app.api.deps import get_current_studio, get_optional_studio, require_studio_user
from app.services.storage_service import tenant_storage
from app.services.cache_service import cache_studio_theme, get_cached_studio_theme, invalidate_studio_cache
from pydantic import BaseModel


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
        custom_css=studio.custom_css
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
