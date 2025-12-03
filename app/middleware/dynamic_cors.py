"""
Dynamic CORS middleware that loads custom domains from database.

This module provides:
1. Caching of verified custom domains from studio_domains table
2. Combined origin checking (static config + database + wildcards)
3. Cache refresh capability for when new domains are verified
"""

import re
import time
import logging
from typing import Set, Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Cache for custom domains
_custom_domains_cache: Set[str] = set()
_cache_timestamp: float = 0
CACHE_TTL = 300  # Refresh cache every 5 minutes


def _load_custom_domains_from_db() -> Set[str]:
    """Load verified custom domains from database."""
    from app.db.session import SessionLocal
    from app.db.models import StudioDomain
    
    domains = set()
    db = SessionLocal()
    try:
        records = db.query(StudioDomain).filter(
            StudioDomain.is_verified == True
        ).all()
        
        for record in records:
            # Add both http and https variants
            domains.add(f"http://{record.domain}")
            domains.add(f"https://{record.domain}")
            # Also add with common ports for development
            domains.add(f"http://{record.domain}:3001")
            domains.add(f"http://{record.domain}:8000")
        
        logger.debug(f"Loaded {len(records)} custom domains from database")
        return domains
    except Exception as e:
        logger.error(f"Failed to load custom domains: {e}")
        return set()
    finally:
        db.close()


def get_custom_domains(force_refresh: bool = False) -> Set[str]:
    """
    Get cached custom domains, refreshing if stale.
    
    Args:
        force_refresh: If True, bypass cache and reload from database
    
    Returns:
        Set of allowed custom domain origins
    """
    global _custom_domains_cache, _cache_timestamp
    
    current_time = time.time()
    
    # Refresh if forced, cache is empty, or TTL expired
    if force_refresh or not _custom_domains_cache or (current_time - _cache_timestamp > CACHE_TTL):
        _custom_domains_cache = _load_custom_domains_from_db()
        _cache_timestamp = current_time
        logger.info(f"CORS cache refreshed: {len(_custom_domains_cache)} custom domains")
    
    return _custom_domains_cache


def refresh_cors_cache() -> int:
    """
    Force refresh the CORS cache.
    
    Call this when a new domain is verified.
    
    Returns:
        Number of custom domains in cache
    """
    domains = get_custom_domains(force_refresh=True)
    return len(domains)


def get_all_allowed_origins() -> Set[str]:
    """
    Get all allowed origins: static config + custom domains.
    
    Returns:
        Combined set of all allowed origins
    """
    settings = get_settings()
    
    # Start with static origins from config
    static_origins = set(settings.cors_origins)
    
    # Add custom domains from database
    custom_domains = get_custom_domains()
    
    return static_origins | custom_domains


def is_origin_allowed(origin: str) -> bool:
    """
    Check if an origin is allowed (supports wildcards + custom domains).
    
    This function checks:
    1. Exact match in static config
    2. Exact match in custom domains from database
    3. Wildcard pattern match (e.g., http://*.photoapp.local:3001)
    
    Args:
        origin: The Origin header value to check
    
    Returns:
        True if origin is allowed, False otherwise
    """
    if not origin:
        return False
    
    allowed_origins = get_all_allowed_origins()
    
    # Check exact match first (fastest)
    if origin in allowed_origins:
        return True
    
    # Check wildcard patterns
    for pattern in allowed_origins:
        if '*' in pattern:
            # Convert wildcard pattern to regex
            # http://*.photoapp.local:3001 -> http://[^:/]+\.photoapp\.local:3001
            regex_pattern = pattern.replace('.', r'\.').replace('*', r'[^:/]+')
            try:
                if re.match(f'^{regex_pattern}$', origin):
                    return True
            except re.error:
                logger.warning(f"Invalid CORS pattern: {pattern}")
                continue
    
    return False


def get_cors_headers(origin: str) -> dict:
    """
    Get CORS headers for a given origin.
    
    Args:
        origin: The Origin header value
    
    Returns:
        Dictionary of CORS headers to add to response
    """
    if not origin or not is_origin_allowed(origin):
        return {}
    
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, Origin, X-Requested-With, Cache-Control, X-Studio-ID",
        "Access-Control-Max-Age": "86400",
        "Vary": "Origin",
    }
