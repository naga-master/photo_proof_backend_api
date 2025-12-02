"""Studio onboarding endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
import re
import os
import base64
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from app.db.session import get_db
from app.db.models import Studio, StudioDomain, User, SubscriptionPlan, StudioSubscription
from app.services.auth_service import AuthService
from app.core.config import get_settings


def save_studio_photo_from_base64(studio_id: str, base64_data: str) -> str:
    """
    Save base64 image data to file system and return the URL path.
    
    Args:
        studio_id: The studio's ID
        base64_data: Base64 encoded image (data:image/jpeg;base64,...)
    
    Returns:
        URL path to the saved image (e.g., /uploads/studios/{studio_id}/photo.jpg)
    """
    settings = get_settings()
    
    # Parse the base64 data
    if not base64_data.startswith('data:image'):
        raise ValueError("Invalid image data format")
    
    # Extract format and data
    header, encoded = base64_data.split(',', 1)
    # Get extension from MIME type (e.g., data:image/jpeg;base64 -> jpeg)
    mime_type = header.split(':')[1].split(';')[0]
    ext_map = {
        'image/jpeg': 'jpg',
        'image/jpg': 'jpg',
        'image/png': 'png',
        'image/gif': 'gif',
        'image/webp': 'webp',
    }
    extension = ext_map.get(mime_type, 'jpg')
    
    # Create directory for studio photos
    studio_dir = Path(settings.uploads_directory) / 'studios' / studio_id
    studio_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    filename = f"studio_photo_{uuid.uuid4().hex[:8]}.{extension}"
    filepath = studio_dir / filename
    
    # Decode and save
    image_data = base64.b64decode(encoded)
    with open(filepath, 'wb') as f:
        f.write(image_data)
    
    # Return relative URL path
    return f"/uploads/studios/{studio_id}/{filename}"


def save_logo_from_base64(studio_id: str, base64_data: str) -> str:
    """
    Save base64 logo image to file system and return the URL path.
    
    Args:
        studio_id: The studio's ID
        base64_data: Base64 encoded image (data:image/png;base64,...)
    
    Returns:
        URL path to the saved logo (e.g., /uploads/studios/{studio_id}/logo.png)
    """
    settings = get_settings()
    
    # Parse the base64 data
    if not base64_data.startswith('data:image'):
        raise ValueError("Invalid image data format")
    
    # Extract format and data
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
    
    # Create directory for studio logos
    studio_dir = Path(settings.uploads_directory) / 'studios' / studio_id
    studio_dir.mkdir(parents=True, exist_ok=True)
    
    # Use consistent filename for logo (overwrites previous)
    filename = f"logo.{extension}"
    filepath = studio_dir / filename
    
    # Decode and save
    image_data = base64.b64decode(encoded)
    with open(filepath, 'wb') as f:
        f.write(image_data)
    
    # Return relative URL path
    return f"/uploads/studios/{studio_id}/{filename}"


router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


# ========== Request Models ==========

class CheckSubdomainRequest(BaseModel):
    subdomain: str = Field(min_length=3, max_length=50)


class OnboardingStartRequest(BaseModel):
    studio_name: str = Field(min_length=2, max_length=100)
    subdomain: str = Field(min_length=3, max_length=50)
    email: EmailStr
    owner_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8)
    phone: str | None = None


class OnboardingBrandingRequest(BaseModel):
    studio_id: str
    brand_color: str = Field(default="#6366F1")
    typography: str = Field(default="System Default (Inter & Cormorant)")
    studio_photo: str | None = None  # Base64 data URL for About page image
    logo: str | None = None          # Base64 data URL for studio logo
    custom_css: str | None = None


class OnboardingDomainRequest(BaseModel):
    studio_id: str
    custom_domain: str | None = None


class OnboardingCompleteRequest(BaseModel):
    studio_id: str
    plan_id: str


# ========== Endpoints ==========

@router.get("/check-subdomain")
async def check_subdomain_availability(
    subdomain: str,
    db: Session = Depends(get_db)
):
    """Check if subdomain is available."""
    
    # Validate subdomain format
    if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', subdomain):
        return {
            "available": False,
            "reason": "Subdomain must contain only lowercase letters, numbers, and hyphens"
        }
    
    # Check if subdomain exists
    existing = db.query(Studio).filter_by(subdomain=subdomain).first()
    
    if existing:
        return {
            "available": False,
            "reason": "This subdomain is already taken"
        }
    
    # Check reserved subdomains
    reserved = ['www', 'api', 'app', 'admin', 'dashboard', 'mail', 'ftp', 'localhost', 'demo', 'alpha', 'beta', 'gamma']
    if subdomain in reserved:
        return {
            "available": False,
            "reason": "This subdomain is reserved"
        }
    
    return {
        "available": True,
        "subdomain": subdomain,
        "full_domain": f"{subdomain}.photoapp.local"
    }


@router.post("/start")
async def start_onboarding(
    data: OnboardingStartRequest,
    db: Session = Depends(get_db)
):
    """Start onboarding - create studio and owner account."""
    
    # Check subdomain availability
    existing = db.query(Studio).filter_by(subdomain=data.subdomain).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subdomain already taken"
        )
    
    # Check email availability
    existing_user = db.query(User).filter_by(email=data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    try:
        # Create studio
        studio = Studio(
            name=data.studio_name,
            email=data.email,
            phone=data.phone,
            subdomain=data.subdomain,
            brand_color="#6366F1",  # Default
            typography="System Default (Inter & Cormorant)",
            onboarding_completed=False,
            onboarding_step="plan",  # Next step
            is_active=True
        )
        db.add(studio)
        db.flush()
        
        # Create studio domain entry
        domain = StudioDomain(
            studio_id=studio.id,
            domain=f"{data.subdomain}.photoapp.local",
            subdomain=data.subdomain,
            is_primary=True,
            is_verified=True,  # Auto-verify local domains
            verified_at=datetime.utcnow()
        )
        db.add(domain)
        
        # Create owner user
        hashed_password = AuthService.hash_password(data.password)
        owner = User(
            email=data.email,
            username=data.email,  # Use email as username
            name=data.owner_name,
            password_hash=hashed_password,  # Correct field name
            role="studio_owner",  # Owner role
            studio_id=studio.id,
            is_active=True
        )
        db.add(owner)
        
        db.commit()
        db.refresh(studio)
        db.refresh(owner)
        
        # Refresh CORS cache to include new subdomain domain
        try:
            from app.middleware.dynamic_cors import refresh_cors_cache
            refresh_cors_cache()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to refresh CORS cache: {e}")
        
        return {
            "studio_id": studio.id,
            "subdomain": studio.subdomain,
            "next_step": "plan",
            "message": "Studio created successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create studio: {str(e)}"
        )


@router.post("/branding")
async def update_branding(
    data: OnboardingBrandingRequest,
    db: Session = Depends(get_db)
):
    """Update studio branding including optional studio photo."""
    
    studio = db.query(Studio).filter_by(id=data.studio_id).first()
    if not studio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Studio not found"
        )
    
    studio.brand_color = data.brand_color
    studio.typography = data.typography
    studio.custom_css = data.custom_css
    studio.onboarding_step = "domain"
    
    # Handle studio photo upload (for About page)
    if data.studio_photo:
        try:
            if data.studio_photo.startswith('data:image'):
                # Base64 encoded image - save to file system
                photo_url = save_studio_photo_from_base64(data.studio_id, data.studio_photo)
                studio.studio_photo = photo_url
            else:
                # Direct URL (external image)
                studio.studio_photo = data.studio_photo
        except Exception as e:
            # Log but don't fail the whole request if photo upload fails
            import logging
            logging.getLogger(__name__).error(f"Failed to save studio photo: {e}")
    
    # Handle logo upload (for branding/invoices)
    if data.logo:
        try:
            if data.logo.startswith('data:image'):
                # Base64 encoded image - save to file system
                logo_url = save_logo_from_base64(data.studio_id, data.logo)
                studio.logo_url = logo_url
            else:
                # Direct URL (external image)
                studio.logo_url = data.logo
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to save logo: {e}")
    
    db.commit()
    
    return {
        "studio_id": studio.id,
        "next_step": "domain",
        "message": "Branding updated successfully"
    }


@router.post("/domain")
async def configure_domain(
    data: OnboardingDomainRequest,
    db: Session = Depends(get_db)
):
    """Configure custom domain (optional)."""
    
    studio = db.query(Studio).filter_by(id=data.studio_id).first()
    if not studio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Studio not found"
        )
    
    if data.custom_domain:
        # Add custom domain
        existing = db.query(StudioDomain).filter_by(domain=data.custom_domain).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Domain already registered"
            )
        
        domain = StudioDomain(
            studio_id=studio.id,
            domain=data.custom_domain,
            is_primary=False,
            is_verified=False  # Requires verification
        )
        db.add(domain)
    
    studio.onboarding_step = "complete"
    db.commit()
    
    return {
        "studio_id": studio.id,
        "next_step": "complete",
        "message": "Domain configuration saved"
    }


@router.post("/complete")
async def complete_onboarding(
    data: OnboardingCompleteRequest,
    db: Session = Depends(get_db)
):
    """Complete onboarding and activate subscription."""
    
    studio = db.query(Studio).filter_by(id=data.studio_id).first()
    if not studio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Studio not found"
        )
    
    plan = db.query(SubscriptionPlan).filter_by(id=data.plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    try:
        # Create subscription (with 14-day trial)
        subscription = StudioSubscription(
            studio_id=studio.id,
            plan_id=plan.id,
            status="trialing",
            trial_ends_at=datetime.utcnow() + timedelta(days=14),
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        db.add(subscription)
        
        # Mark onboarding complete
        studio.onboarding_completed = True
        studio.onboarding_step = "completed"
        studio.subscription_tier = plan.name
        studio.max_projects = plan.max_projects
        studio.max_storage_gb = plan.max_storage_gb
        
        db.commit()
        db.refresh(studio)
        
        return {
            "studio_id": studio.id,
            "subdomain": studio.subdomain,
            "plan": plan.name,
            "trial_days": 14,
            "message": "Onboarding completed successfully!",
            "redirect_url": f"http://{studio.subdomain}.photoapp.local:3001/dashboard"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete onboarding: {str(e)}"
        )


@router.get("/status/{studio_id}")
async def get_onboarding_status(
    studio_id: str,
    db: Session = Depends(get_db)
):
    """Get current onboarding status."""
    
    studio = db.query(Studio).filter_by(id=studio_id).first()
    if not studio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Studio not found"
        )
    
    return {
        "studio_id": studio.id,
        "current_step": studio.onboarding_step,
        "completed": studio.onboarding_completed,
        "studio_name": studio.name,
        "subdomain": studio.subdomain
    }


# ========== Domain Verification Endpoints ==========

class VerifyDomainRequest(BaseModel):
    domain_id: str


@router.post("/domain/verify")
async def verify_custom_domain(
    data: VerifyDomainRequest,
    db: Session = Depends(get_db)
):
    """
    Verify a custom domain and update CORS cache.
    
    This endpoint should be called after the studio owner has configured
    their DNS records. It verifies the domain and automatically updates
    the CORS allowed origins.
    """
    from app.middleware.dynamic_cors import refresh_cors_cache
    
    domain = db.query(StudioDomain).filter_by(id=data.domain_id).first()
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found"
        )
    
    if domain.is_verified:
        return {
            "verified": True,
            "message": "Domain is already verified"
        }
    
    # TODO: Add actual DNS verification logic here
    # For now, we'll auto-verify for development
    # In production, implement DNS TXT record verification
    
    # Mark domain as verified
    domain.is_verified = True
    domain.verified_at = datetime.utcnow()
    db.commit()
    
    # Refresh CORS cache to include new domain
    num_domains = refresh_cors_cache()
    
    return {
        "verified": True,
        "domain": domain.domain,
        "message": "Domain verified successfully! CORS updated.",
        "cors_domains_cached": num_domains
    }


@router.post("/cors/refresh")
async def refresh_cors_origins():
    """
    Force refresh the CORS cache.
    
    Call this endpoint after manually adding/verifying domains in the database.
    This is useful for admin operations.
    """
    from app.middleware.dynamic_cors import refresh_cors_cache, get_all_allowed_origins
    
    num_domains = refresh_cors_cache()
    all_origins = get_all_allowed_origins()
    
    return {
        "message": "CORS cache refreshed successfully",
        "custom_domains_cached": num_domains,
        "total_allowed_origins": len(all_origins),
        "origins_sample": list(all_origins)[:10]  # Show first 10 for debugging
    }


@router.get("/domains/{studio_id}")
async def get_studio_domains(
    studio_id: str,
    db: Session = Depends(get_db)
):
    """Get all domains configured for a studio."""
    
    studio = db.query(Studio).filter_by(id=studio_id).first()
    if not studio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Studio not found"
        )
    
    domains = db.query(StudioDomain).filter_by(studio_id=studio_id).all()
    
    return {
        "studio_id": studio_id,
        "domains": [
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
    }
