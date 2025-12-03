"""Security headers middleware for production environments."""

from fastapi import Request
from starlette.responses import Response
from app.core.config import get_settings


async def security_headers_middleware(request: Request, call_next) -> Response:
    """
    Add security headers to responses.
    
    Headers are only added in production environment to avoid
    development issues with HTTPS requirements.
    
    Headers added:
    - Strict-Transport-Security (HSTS): Forces HTTPS for 1 year
    - X-Frame-Options: Prevents clickjacking
    - X-Content-Type-Options: Prevents MIME sniffing
    - X-XSS-Protection: Legacy XSS protection
    - Referrer-Policy: Controls referrer information
    """
    response = await call_next(request)
    settings = get_settings()
    
    # Only add strict security headers in production
    if settings.environment == "production":
        # HSTS - Force HTTPS for 1 year, include subdomains
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Prevent clickjacking - don't allow embedding in iframes
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS protection (legacy, but still useful for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Control referrer information sent with requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy - disable unnecessary browser features
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    return response
