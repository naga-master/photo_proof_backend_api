"""Network test endpoint for performance-based network detection."""

from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter(prefix="/network-test", tags=["network"])


@router.get("")
async def network_test():
    """
    Serve a ~100KB test payload for network speed detection.
    
    Returns random binary data with no-cache headers to ensure
    accurate network speed measurement.
    """
    # Generate ~100KB of data (100 * 1024 bytes)
    test_data = b"x" * (100 * 1024)
    
    return Response(
        content=test_data,
        media_type="application/octet-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Content-Length": str(len(test_data)),
        }
    )
