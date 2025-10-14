"""Delivery service for file sharing and download management."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.schemas.deliveries import (
    DeliveryPackage,
    DeliveryRequest,
    DownloadLink,
    DeliveryTracking
)


class DeliveryService:
    """Service for managing file deliveries and downloads."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_delivery_package(self, studio_id: str, request: DeliveryRequest) -> DeliveryPackage:
        """Create a new delivery package."""
        package = DeliveryPackage(
            id=f"pkg_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            name=request.name,
            studio_id=studio_id,
            project_id=request.project_id,
            client_id=request.client_id,
            files=request.files,
            download_limit=request.download_limit,
            expires_at=request.expires_at,
            created_at=datetime.utcnow()
        )
        
        return package
    
    def generate_download_link(self, package_id: str) -> DownloadLink:
        """Generate secure download link."""
        link = DownloadLink(
            id=f"link_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            package_id=package_id,
            url=f"/downloads/{package_id}",
            expires_at=datetime.utcnow() + timedelta(days=7),
            created_at=datetime.utcnow()
        )
        
        return link
    
    def track_download(self, link_id: str, client_info: Dict[str, Any]) -> DeliveryTracking:
        """Track download activity."""
        tracking = DeliveryTracking(
            id=f"track_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            link_id=link_id,
            client_ip=client_info.get("ip"),
            user_agent=client_info.get("user_agent"),
            downloaded_at=datetime.utcnow()
        )
        
        return tracking