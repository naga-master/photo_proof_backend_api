"""Storage service with local and S3 support and tenant isolation."""

import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional
from datetime import datetime, timedelta
import secrets
import uuid
import logging
from PIL import Image

logger = logging.getLogger(__name__)


class StorageService(ABC):
    """Abstract storage service interface."""
    
    @abstractmethod
    async def save_file(self, file: BinaryIO, destination_path: str) -> str:
        """Save file and return URL."""
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file."""
        pass
    
    @abstractmethod
    async def get_presigned_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Get presigned URL for file upload."""
        pass
    
    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        pass


class LocalStorageService(StorageService):
    """Local filesystem storage implementation."""
    
    def __init__(self, base_path: str = "/Users/ns632@apac.comcast.com/Documents/v0_photo_proof/photo_proof_api/uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def save_file(self, file: BinaryIO, destination_path: str) -> str:
        """Save file to local filesystem."""
        full_path = self.base_path / destination_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "wb") as f:
            shutil.copyfileobj(file, f)
        
        # Return URL (relative path for serving)
        return f"/uploads/{destination_path}"
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from local filesystem."""
        # Remove /uploads/ prefix if present
        clean_path = file_path.removeprefix("/uploads/").removeprefix("uploads/")
        full_path = self.base_path / clean_path
        
        if full_path.exists():
            full_path.unlink()
            return True
        
        return False
    
    async def get_presigned_url(self, file_path: str, expires_in: int = 3600) -> str:
        """
        Generate presigned URL for local storage.
        In local mode, we just return the upload endpoint with a token.
        """
        # This will be handled by upload token system
        return f"/api/upload/{file_path}"
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists locally."""
        # Remove /uploads/ prefix if present
        clean_path = file_path.removeprefix("/uploads/").removeprefix("uploads/")
        full_path = self.base_path / clean_path
        return full_path.exists()
    
    def get_full_path(self, relative_path: str) -> Path:
        """Get full filesystem path."""
        # Remove /uploads/ prefix if present (don't use lstrip - it removes characters, not strings!)
        clean_path = relative_path.removeprefix("/uploads/").removeprefix("uploads/")
        return self.base_path / clean_path


class S3StorageService(StorageService):
    """
    S3 storage implementation (placeholder for future).
    
    To implement:
    1. Install boto3: pip install boto3
    2. Configure AWS credentials
    3. Implement methods using boto3 client
    """
    
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.region = region
        # self.s3_client = boto3.client('s3', region_name=region)
    
    async def save_file(self, file: BinaryIO, destination_path: str) -> str:
        """Save file to S3."""
        # Implementation:
        # self.s3_client.upload_fileobj(file, self.bucket_name, destination_path)
        # return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{destination_path}"
        raise NotImplementedError("S3 storage not yet implemented")
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from S3."""
        # Implementation:
        # self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_path)
        raise NotImplementedError("S3 storage not yet implemented")
    
    async def get_presigned_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Generate presigned URL for S3 upload."""
        # Implementation:
        # return self.s3_client.generate_presigned_url(
        #     'put_object',
        #     Params={'Bucket': self.bucket_name, 'Key': file_path},
        #     ExpiresIn=expires_in
        # )
        raise NotImplementedError("S3 storage not yet implemented")
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in S3."""
        # Implementation:
        # try:
        #     self.s3_client.head_object(Bucket=self.bucket_name, Key=file_path)
        #     return True
        # except:
        #     return False
        raise NotImplementedError("S3 storage not yet implemented")


# Storage factory
def get_storage_service(use_s3: bool = False) -> StorageService:
    """Get storage service instance."""
    if use_s3:
        # TODO: Get from environment variables
        return S3StorageService(bucket_name="photo-proof-uploads")
    else:
        return LocalStorageService()


# ========== Multi-Tenant Storage Service ==========

class TenantStorageService:
    """Storage service with automatic tenant isolation.
    
    Directory structure:
    uploads/
    ├── studios/
    │   ├── studio-uuid-1/
    │   │   ├── photos/
    │   │   │   ├── original/
    │   │   │   ├── thumbnails/
    │   │   │   └── variants/
    │   │   ├── logos/
    │   │   └── temp/
    │   ├── studio-uuid-2/
    │   │   └── ...
    └── system/
        └── defaults/
    """
    
    def __init__(self, base_path: str = "uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"TenantStorageService initialized: {self.base_path.absolute()}")
    
    def get_studio_path(self, studio_id: str) -> Path:
        """Get base path for studio's files.
        
        Args:
            studio_id: Studio UUID
            
        Returns:
            Path to studio's directory
        """
        studio_path = self.base_path / "studios" / studio_id
        studio_path.mkdir(parents=True, exist_ok=True)
        return studio_path
    
    def save_photo(
        self,
        file: BinaryIO,
        studio_id: str,
        project_id: int,
        original_filename: str,
        generate_variants: bool = True
    ) -> dict:
        """Save photo with automatic variant generation.
        
        Args:
            file: File object to save
            studio_id: Studio UUID
            project_id: Project ID
            original_filename: Original filename
            generate_variants: Whether to generate thumbnails/variants
            
        Returns:
            Dictionary with file paths and URLs
        """
        # Generate unique filename
        file_ext = Path(original_filename).suffix.lower()
        unique_name = f"{uuid.uuid4()}{file_ext}"
        
        # Studio-specific paths
        studio_path = self.get_studio_path(studio_id)
        original_path = studio_path / "photos" / "original" / unique_name
        thumbnail_path = studio_path / "photos" / "thumbnails" / unique_name
        
        original_path.parent.mkdir(parents=True, exist_ok=True)
        thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save original
        with open(original_path, "wb") as f:
            shutil.copyfileobj(file, f)
        
        logger.info(f"Saved photo for studio {studio_id}: {unique_name}")
        
        result = {
            "original": str(original_path.relative_to(self.base_path)),
            "original_url": f"/uploads/{original_path.relative_to(self.base_path)}",
            "filename": unique_name,
        }
        
        # Generate thumbnail and variants
        if generate_variants:
            try:
                with Image.open(original_path) as img:
                    # Get original dimensions
                    result["width"] = img.width
                    result["height"] = img.height
                    
                    # Thumbnail (400px max dimension)
                    thumb = img.copy()
                    thumb.thumbnail((400, 400), Image.Resampling.LANCZOS)
                    thumb.save(thumbnail_path, quality=85, optimize=True)
                    
                    result["thumbnail"] = str(thumbnail_path.relative_to(self.base_path))
                    result["thumbnail_url"] = f"/uploads/{thumbnail_path.relative_to(self.base_path)}"
                    
                    logger.debug(f"Generated thumbnail: {unique_name}")
            except Exception as e:
                logger.error(f"Failed to generate thumbnail for {unique_name}: {e}")
        
        return result
    
    def save_logo(
        self,
        file: BinaryIO,
        studio_id: str,
        original_filename: str
    ) -> dict:
        """Save studio logo.
        
        Args:
            file: File object to save
            studio_id: Studio UUID
            original_filename: Original filename
            
        Returns:
            Dictionary with file paths and URLs
        """
        file_ext = Path(original_filename).suffix.lower()
        unique_name = f"logo_{uuid.uuid4()}{file_ext}"
        
        studio_path = self.get_studio_path(studio_id)
        logo_path = studio_path / "logos" / unique_name
        logo_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save logo
        with open(logo_path, "wb") as f:
            shutil.copyfileobj(file, f)
        
        logger.info(f"Saved logo for studio {studio_id}: {unique_name}")
        
        return {
            "path": str(logo_path.relative_to(self.base_path)),
            "url": f"/uploads/{logo_path.relative_to(self.base_path)}",
            "filename": unique_name,
        }
    
    def delete_file(self, studio_id: str, file_path: str) -> bool:
        """Delete a file (with security check).
        
        Args:
            studio_id: Studio UUID (for security verification)
            file_path: Relative path to file
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            full_path = self.base_path / file_path
            studio_path = self.get_studio_path(studio_id)
            
            # Security check: Verify path is within studio directory
            if not str(full_path).startswith(str(studio_path)):
                logger.error(f"🚨 Security violation: Attempted to delete file outside studio directory")
                logger.error(f"   Studio: {studio_id}, Path: {file_path}")
                return False
            
            if full_path.exists():
                full_path.unlink()
                logger.info(f"Deleted file for studio {studio_id}: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    def get_studio_storage_usage(self, studio_id: str) -> int:
        """Calculate total storage used by studio (in bytes).
        
        Args:
            studio_id: Studio UUID
            
        Returns:
            Total storage used in bytes
        """
        studio_path = self.get_studio_path(studio_id)
        total_size = 0
        
        try:
            for dirpath, dirnames, filenames in os.walk(studio_path):
                for filename in filenames:
                    filepath = Path(dirpath) / filename
                    if filepath.exists():
                        total_size += filepath.stat().st_size
        except Exception as e:
            logger.error(f"Error calculating storage for studio {studio_id}: {e}")
        
        return total_size
    
    def check_storage_quota(self, studio_id: str, max_gb: int) -> tuple[bool, int, int]:
        """Check if studio is within storage quota.
        
        Args:
            studio_id: Studio UUID
            max_gb: Maximum allowed storage in GB
            
        Returns:
            Tuple of (within_quota, used_bytes, max_bytes)
        """
        used_bytes = self.get_studio_storage_usage(studio_id)
        max_bytes = max_gb * 1024 * 1024 * 1024
        within_quota = used_bytes < max_bytes
        
        return within_quota, used_bytes, max_bytes
    
    def get_storage_stats(self, studio_id: str) -> dict:
        """Get detailed storage statistics for a studio.
        
        Args:
            studio_id: Studio UUID
            
        Returns:
            Dictionary with storage statistics
        """
        studio_path = self.get_studio_path(studio_id)
        
        stats = {
            "total_bytes": 0,
            "photo_count": 0,
            "logo_count": 0,
            "other_count": 0,
        }
        
        try:
            for dirpath, dirnames, filenames in os.walk(studio_path):
                dirpath_obj = Path(dirpath)
                
                for filename in filenames:
                    filepath = dirpath_obj / filename
                    if filepath.exists():
                        file_size = filepath.stat().st_size
                        stats["total_bytes"] += file_size
                        
                        # Categorize files
                        if "photos" in str(dirpath):
                            stats["photo_count"] += 1
                        elif "logos" in str(dirpath):
                            stats["logo_count"] += 1
                        else:
                            stats["other_count"] += 1
                            
        except Exception as e:
            logger.error(f"Error getting storage stats for studio {studio_id}: {e}")
        
        # Convert to human-readable
        stats["total_mb"] = stats["total_bytes"] / (1024 * 1024)
        stats["total_gb"] = stats["total_bytes"] / (1024 * 1024 * 1024)
        
        return stats


# Global tenant storage instance
tenant_storage = TenantStorageService()
