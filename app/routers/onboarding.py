"""Studio onboarding endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
import re
from datetime import datetime, timedelta

from app.db.session import get_db
from app.db.models import Studio, StudioDomain, User, SubscriptionPlan, StudioSubscription
from app.services.auth_service import AuthService

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
    """Update studio branding."""
    
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
