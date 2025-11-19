"""File serving router with proper CORS headers."""

import re
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


def origin_matches_pattern(origin: str, patterns: list[str]) -> bool:
    """Check if origin matches any of the allowed patterns (supports wildcards)."""
    for pattern in patterns:
        if pattern == origin:
            return True
        # Convert wildcard pattern to regex
        if '*' in pattern:
            regex_pattern = pattern.replace('.', r'\.').replace('*', r'[^:/]+')
            if re.match(f'^{regex_pattern}$', origin):
                return True
    return False


@router.get("/uploads/{path:path}")
@router.head("/uploads/{path:path}")
async def serve_upload_file(path: str, request: Request):
    """
    Serve uploaded files with proper CORS headers.
    
    This endpoint ensures CORS headers are applied to static file requests,
    which is necessary for frontend fetch/download functionality.
    
    Supports both GET and HEAD methods for proper browser compatibility.
    """
    uploads_dir = Path(settings.uploads_directory)
    file_path = uploads_dir / path
    
    # Security: Prevent directory traversal
    try:
        file_path = file_path.resolve()
        uploads_dir = uploads_dir.resolve()
        
        if not str(file_path).startswith(str(uploads_dir)):
            raise HTTPException(status_code=403, detail="Access denied")
            
    except (ValueError, OSError):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    # Check if file exists
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get origin from request
    origin = request.headers.get("origin", "")
    
    # Prepare CORS headers with wildcard pattern matching
    cors_headers = {}
    if origin and origin_matches_pattern(origin, settings.cors_origins):
        cors_headers["Access-Control-Allow-Origin"] = origin
        cors_headers["Access-Control-Allow-Credentials"] = "true"
        cors_headers["Access-Control-Allow-Methods"] = "*"
        cors_headers["Access-Control-Allow-Headers"] = "*"
    
    # Return file with proper headers including CORS
    return FileResponse(
        path=file_path,
        media_type="image/jpeg",  # You can make this dynamic based on extension
        headers={
            "Cache-Control": "public, max-age=31536000",  # Cache for 1 year
            "Accept-Ranges": "bytes",
            **cors_headers,  # Add CORS headers
        }
    )
