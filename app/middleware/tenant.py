"""Multi-tenant middleware for domain-based studio detection."""

import logging
from typing import Optional
from fastapi import Request
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Studio, StudioDomain

logger = logging.getLogger(__name__)


class TenantContext:
    """Thread-safe tenant context using request state."""
    
    @staticmethod
    def get_studio_id_from_request(request: Request) -> Optional[str]:
        """Get studio_id from request state."""
        return getattr(request.state, 'studio_id', None)
    
    @staticmethod
    def get_studio_from_request(request: Request) -> Optional[Studio]:
        """Get full studio object from request state."""
        return getattr(request.state, 'studio', None)


async def detect_studio_from_host(host: str, db: Session) -> Optional[Studio]:
    """Detect studio from HTTP Host header.
    
    Args:
        host: HTTP Host header value (e.g., "mystudio.photoapp.com" or "photos.mystudio.com")
        db: Database session
    
    Returns:
        Studio object if found, None otherwise
    """
    
    # Remove port if present
    clean_host = host.split(':')[0].lower()
    
    logger.debug(f"Detecting studio from host: {clean_host}")
    
    # DEVELOPMENT FALLBACK: If accessing via localhost/127.0.0.1, use demo studio
    if clean_host in ['localhost', '127.0.0.1']:
        logger.info(f"🔧 Development mode: Using 'demo' studio for localhost")
        studio = db.query(Studio).filter(
            Studio.subdomain == 'demo',
            Studio.is_active == True
        ).first()
        
        if studio:
            logger.info(f"✅ Found demo studio for localhost: {studio.name}")
            return studio
        else:
            logger.warning(f"⚠️  No 'demo' studio found for localhost fallback")
            # Continue with normal detection (will return None)
    
    # 1. Check custom domain (photos.mystudio.com)
    domain_record = db.query(StudioDomain).filter(
        StudioDomain.domain == clean_host,
        StudioDomain.is_verified == True
    ).first()
    
    if domain_record:
        logger.info(f"✅ Found studio via custom domain: {domain_record.studio_id}")
        return domain_record.studio
    
    # 2. Check subdomain (mystudio.photoapp.com)
    if '.' in clean_host:
        subdomain = clean_host.split('.')[0]
        
        # Check StudioDomain table with subdomain
        domain_by_subdomain = db.query(StudioDomain).filter(
            StudioDomain.subdomain == subdomain,
            StudioDomain.is_verified == True
        ).first()
        
        if domain_by_subdomain:
            logger.info(f"✅ Found studio via StudioDomain subdomain: {subdomain}")
            return domain_by_subdomain.studio
        
        # Fallback: check studio.subdomain field directly (for backward compatibility)
        studio = db.query(Studio).filter(
            Studio.subdomain == subdomain,
            Studio.is_active == True
        ).first()
        
        if studio:
            logger.info(f"✅ Found studio via Studio.subdomain: {subdomain}")
            return studio
    
    logger.warning(f"⚠️  No studio found for host: {clean_host}")
    return None


async def tenant_middleware(request: Request, call_next):
    """Middleware to detect and set current tenant (studio).
    
    This middleware:
    1. Extracts the Host header from the request
    2. Determines which studio the request is for
    3. Sets studio information in request.state
    4. Passes request to the next handler
    
    Routes that should skip tenant detection are listed in skip_paths.
    """
    
    # Skip tenant detection for OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        logger.debug("Skipping tenant detection for OPTIONS request")
        return await call_next(request)
    
    # Skip tenant detection for certain paths
    skip_paths = [
        '/docs',
        '/redoc',
        '/openapi.json',
        '/api/health',
        '/api/v1/health',
        '/api/onboarding',
        '/api/auth',  # Skip all auth endpoints (login, register, etc.)
        '/_',  # Internal routes
    ]
    
    # Check if path should skip tenant detection
    path = request.url.path
    if any(path.startswith(skip_path) for skip_path in skip_paths):
        logger.debug(f"Skipping tenant detection for path: {path}")
        return await call_next(request)
    
    # Get host header
    host = request.headers.get('host', '')
    
    if not host:
        # No host header, continue without tenant
        logger.debug("No host header present, continuing without tenant")
        request.state.studio_id = None
        request.state.studio = None
        return await call_next(request)
    
    # Detect studio from host
    db = SessionLocal()
    try:
        studio = await detect_studio_from_host(host, db)
        
        if studio:
            # Set studio in request state for downstream use
            request.state.studio_id = studio.id
            request.state.studio = studio
            logger.debug(f"📍 Request for studio: {studio.name} ({studio.id})")
            
            # Add custom header to response (useful for debugging)
            response = await call_next(request)
            response.headers["X-Studio-ID"] = studio.id
            response.headers["X-Studio-Name"] = studio.name
            return response
        else:
            # No studio found for this host
            request.state.studio_id = None
            request.state.studio = None
            logger.debug(f"No studio found for host: {host}")
            return await call_next(request)
            
    except Exception as e:
        logger.error(f"Error in tenant middleware: {e}", exc_info=True)
        # Continue without tenant on error
        request.state.studio_id = None
        request.state.studio = None
        return await call_next(request)
    finally:
        db.close()
