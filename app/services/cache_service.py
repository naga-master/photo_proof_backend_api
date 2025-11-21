"""Simple in-memory cache as Redis alternative.

This cache service provides thread-safe caching with TTL support.
It's designed to cache studio themes, user sessions, and other frequently accessed data.
"""

from typing import Any, Optional, Callable
from datetime import datetime, timedelta
import threading
import functools
import logging

logger = logging.getLogger(__name__)


class InMemoryCache:
    """Thread-safe in-memory cache with TTL support."""
    
    def __init__(self):
        self._cache: dict[str, Any] = {}
        self._expiry: dict[str, datetime] = {}
        self._lock = threading.RLock()
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set cache value with TTL in seconds.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 3600 = 1 hour)
        """
        with self._lock:
            self._cache[key] = value
            self._expiry[key] = datetime.now() + timedelta(seconds=ttl)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
    
    def get(self, key: str) -> Optional[Any]:
        """Get cache value if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if exists and not expired, None otherwise
        """
        with self._lock:
            if key in self._cache:
                if datetime.now() < self._expiry[key]:
                    logger.debug(f"Cache HIT: {key}")
                    return self._cache[key]
                else:
                    # Expired, remove it
                    del self._cache[key]
                    del self._expiry[key]
                    logger.debug(f"Cache EXPIRED: {key}")
            
            logger.debug(f"Cache MISS: {key}")
            return None
    
    def delete(self, key: str):
        """Delete cache entry.
        
        Args:
            key: Cache key to delete
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._expiry[key]
                logger.debug(f"Cache DELETE: {key}")
    
    def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern (simple prefix matching).
        
        Args:
            pattern: Key prefix to match (e.g., "studio:123:")
        """
        with self._lock:
            keys_to_delete = [key for key in self._cache.keys() if key.startswith(pattern)]
            for key in keys_to_delete:
                del self._cache[key]
                del self._expiry[key]
            
            if keys_to_delete:
                logger.info(f"Cache DELETE_PATTERN: {pattern} ({len(keys_to_delete)} keys)")
    
    def clear(self):
        """Clear entire cache."""
        with self._lock:
            self._cache.clear()
            self._expiry.clear()
            logger.info("Cache cleared")
    
    def cleanup_expired(self):
        """Remove all expired entries.
        
        This should be called periodically (e.g., every hour) to prevent memory leaks.
        """
        with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, exp_time in self._expiry.items()
                if now >= exp_time
            ]
            for key in expired_keys:
                del self._cache[key]
                del self._expiry[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
    
    def get_stats(self) -> dict:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats (size, expired count, etc.)
        """
        with self._lock:
            now = datetime.now()
            total_entries = len(self._cache)
            expired_entries = sum(1 for exp_time in self._expiry.values() if now >= exp_time)
            active_entries = total_entries - expired_entries
            
            return {
                "total_entries": total_entries,
                "active_entries": active_entries,
                "expired_entries": expired_entries,
            }


# Global cache instance
cache = InMemoryCache()


def cached(ttl: int = 3600, key_prefix: str = ""):
    """Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
        
    Example:
        @cached(ttl=1800, key_prefix="studio")
        def get_studio_theme(studio_id: str):
            return db.query(Studio).filter_by(id=studio_id).first()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try cache first
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


# Convenience functions for common operations

def cache_studio_theme(studio_id: str, theme_data: dict, ttl: int = 1800):
    """Cache studio theme data (30 minutes default).
    
    Args:
        studio_id: Studio ID
        theme_data: Theme configuration dictionary
        ttl: Time to live in seconds (default: 1800 = 30 minutes)
    """
    cache.set(f"studio:theme:{studio_id}", theme_data, ttl)


def get_cached_studio_theme(studio_id: str) -> Optional[dict]:
    """Get cached studio theme data.
    
    Args:
        studio_id: Studio ID
        
    Returns:
        Theme data dictionary if cached, None otherwise
    """
    return cache.get(f"studio:theme:{studio_id}")


def invalidate_studio_cache(studio_id: str):
    """Invalidate all cache entries for a studio.
    
    Args:
        studio_id: Studio ID
    """
    cache.delete_pattern(f"studio:theme:{studio_id}")
    cache.delete_pattern(f"studio:config:{studio_id}")
    logger.info(f"Invalidated cache for studio: {studio_id}")


# Background task to clean up expired entries
def start_cache_cleanup_task(interval_seconds: int = 3600):
    """Start background task to clean up expired cache entries.
    
    Args:
        interval_seconds: Cleanup interval in seconds (default: 3600 = 1 hour)
    """
    import threading
    import time
    
    def cleanup_loop():
        while True:
            time.sleep(interval_seconds)
            try:
                cleaned = cache.cleanup_expired()
                logger.info(f"Cache cleanup completed: {cleaned} entries removed")
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}", exc_info=True)
    
    thread = threading.Thread(target=cleanup_loop, daemon=True, name="CacheCleanup")
    thread.start()
    logger.info(f"✅ Cache cleanup task started (interval: {interval_seconds}s)")
