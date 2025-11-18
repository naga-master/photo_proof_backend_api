"""Storage service with local and S3 support."""

import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional
from datetime import datetime, timedelta
import secrets


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
