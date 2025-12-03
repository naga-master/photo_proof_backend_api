"""
Storage Service Tests - Tests for local and tenant storage services.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from io import BytesIO
from PIL import Image

from app.services.storage_service import (
    LocalStorageService,
    TenantStorageService,
    get_storage_service,
)


class TestLocalStorageService:
    """Test LocalStorageService functionality."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        service = LocalStorageService(base_path=temp_dir)
        yield service
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def sample_file(self):
        """Create a sample file for testing."""
        return BytesIO(b"test file content")

    @pytest.mark.asyncio
    async def test_save_file(self, temp_storage, sample_file):
        """Test saving a file."""
        url = await temp_storage.save_file(sample_file, "test/file.txt")
        
        assert url == "/uploads/test/file.txt"
        assert (temp_storage.base_path / "test" / "file.txt").exists()

    @pytest.mark.asyncio
    async def test_save_file_creates_directories(self, temp_storage, sample_file):
        """Test that save_file creates parent directories."""
        await temp_storage.save_file(sample_file, "deep/nested/path/file.txt")
        
        assert (temp_storage.base_path / "deep" / "nested" / "path" / "file.txt").exists()

    @pytest.mark.asyncio
    async def test_delete_file(self, temp_storage, sample_file):
        """Test deleting a file."""
        await temp_storage.save_file(sample_file, "to_delete.txt")
        
        result = await temp_storage.delete_file("/uploads/to_delete.txt")
        
        assert result is True
        assert not (temp_storage.base_path / "to_delete.txt").exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self, temp_storage):
        """Test deleting a file that doesn't exist."""
        result = await temp_storage.delete_file("/uploads/nonexistent.txt")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_file_exists(self, temp_storage, sample_file):
        """Test checking if file exists."""
        await temp_storage.save_file(sample_file, "exists.txt")
        
        assert await temp_storage.file_exists("exists.txt") is True
        assert await temp_storage.file_exists("nonexistent.txt") is False

    @pytest.mark.asyncio
    async def test_file_exists_with_uploads_prefix(self, temp_storage, sample_file):
        """Test file_exists handles /uploads/ prefix."""
        await temp_storage.save_file(sample_file, "prefixed.txt")
        
        assert await temp_storage.file_exists("/uploads/prefixed.txt") is True
        assert await temp_storage.file_exists("uploads/prefixed.txt") is True

    def test_get_full_path(self, temp_storage):
        """Test get_full_path returns correct path."""
        path = temp_storage.get_full_path("/uploads/test/file.jpg")
        
        assert path == temp_storage.base_path / "test" / "file.jpg"

    def test_get_full_path_strips_prefix(self, temp_storage):
        """Test get_full_path removes uploads prefix."""
        path1 = temp_storage.get_full_path("/uploads/file.jpg")
        path2 = temp_storage.get_full_path("uploads/file.jpg")
        path3 = temp_storage.get_full_path("file.jpg")
        
        assert path1 == path2 == path3

    @pytest.mark.asyncio
    async def test_get_presigned_url(self, temp_storage):
        """Test presigned URL generation."""
        url = await temp_storage.get_presigned_url("test/photo.jpg")
        
        assert url == "/api/upload/test/photo.jpg"


class TestTenantStorageService:
    """Test TenantStorageService functionality."""

    @pytest.fixture
    def temp_tenant_storage(self):
        """Create temporary tenant storage."""
        temp_dir = tempfile.mkdtemp()
        service = TenantStorageService(base_path=temp_dir)
        yield service
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def sample_image(self):
        """Create a sample image for testing."""
        img = Image.new('RGB', (800, 600), color='red')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        return buffer

    @pytest.fixture
    def sample_file(self):
        """Create a sample file for testing."""
        return BytesIO(b"logo content")

    def test_get_studio_path(self, temp_tenant_storage):
        """Test studio path generation."""
        studio_id = "studio-123"
        path = temp_tenant_storage.get_studio_path(studio_id)
        
        assert path == temp_tenant_storage.base_path / "studios" / studio_id
        assert path.exists()

    def test_get_studio_path_creates_directory(self, temp_tenant_storage):
        """Test that get_studio_path creates the directory."""
        studio_id = "new-studio"
        path = temp_tenant_storage.get_studio_path(studio_id)
        
        assert path.exists()
        assert path.is_dir()

    def test_save_photo(self, temp_tenant_storage, sample_image):
        """Test saving a photo with variants."""
        result = temp_tenant_storage.save_photo(
            file=sample_image,
            studio_id="studio-123",
            project_id=1,
            original_filename="test.jpg",
            generate_variants=True
        )
        
        assert "original" in result
        assert "original_url" in result
        assert "filename" in result
        assert "thumbnail" in result
        assert "thumbnail_url" in result
        assert "width" in result
        assert "height" in result
        
        # Verify files exist
        original_path = temp_tenant_storage.base_path / result["original"]
        assert original_path.exists()
        
        thumbnail_path = temp_tenant_storage.base_path / result["thumbnail"]
        assert thumbnail_path.exists()

    def test_save_photo_without_variants(self, temp_tenant_storage, sample_image):
        """Test saving a photo without generating variants."""
        result = temp_tenant_storage.save_photo(
            file=sample_image,
            studio_id="studio-123",
            project_id=1,
            original_filename="test.jpg",
            generate_variants=False
        )
        
        assert "original" in result
        assert "thumbnail" not in result

    def test_save_photo_unique_filename(self, temp_tenant_storage, sample_image):
        """Test that saved photos get unique filenames."""
        result1 = temp_tenant_storage.save_photo(
            file=sample_image,
            studio_id="studio-123",
            project_id=1,
            original_filename="test.jpg",
            generate_variants=False
        )
        
        sample_image.seek(0)
        result2 = temp_tenant_storage.save_photo(
            file=sample_image,
            studio_id="studio-123",
            project_id=1,
            original_filename="test.jpg",
            generate_variants=False
        )
        
        assert result1["filename"] != result2["filename"]

    def test_save_logo(self, temp_tenant_storage, sample_file):
        """Test saving a studio logo."""
        result = temp_tenant_storage.save_logo(
            file=sample_file,
            studio_id="studio-123",
            original_filename="logo.png"
        )
        
        assert "path" in result
        assert "url" in result
        assert "filename" in result
        assert result["filename"].startswith("logo_")
        
        # Verify file exists
        logo_path = temp_tenant_storage.base_path / result["path"]
        assert logo_path.exists()

    def test_delete_file_success(self, temp_tenant_storage, sample_file):
        """Test deleting a file within studio directory."""
        # Save a file first
        result = temp_tenant_storage.save_logo(
            file=sample_file,
            studio_id="studio-123",
            original_filename="to_delete.png"
        )
        
        # Delete it
        deleted = temp_tenant_storage.delete_file("studio-123", result["path"])
        
        assert deleted is True
        assert not (temp_tenant_storage.base_path / result["path"]).exists()

    def test_delete_file_security_check(self, temp_tenant_storage, sample_file):
        """Test that delete_file prevents cross-tenant access."""
        # Save a file for studio-1
        result = temp_tenant_storage.save_logo(
            file=sample_file,
            studio_id="studio-1",
            original_filename="secret.png"
        )
        
        # Try to delete it as studio-2 (should fail)
        deleted = temp_tenant_storage.delete_file("studio-2", result["path"])
        
        assert deleted is False
        # File should still exist
        assert (temp_tenant_storage.base_path / result["path"]).exists()

    def test_get_studio_storage_usage(self, temp_tenant_storage, sample_image):
        """Test calculating storage usage."""
        studio_id = "studio-123"
        
        # Save some files
        temp_tenant_storage.save_photo(
            file=sample_image,
            studio_id=studio_id,
            project_id=1,
            original_filename="photo1.jpg",
            generate_variants=False
        )
        
        sample_image.seek(0)
        temp_tenant_storage.save_photo(
            file=sample_image,
            studio_id=studio_id,
            project_id=1,
            original_filename="photo2.jpg",
            generate_variants=False
        )
        
        usage = temp_tenant_storage.get_studio_storage_usage(studio_id)
        
        assert usage > 0

    def test_get_studio_storage_usage_empty(self, temp_tenant_storage):
        """Test storage usage for empty studio."""
        usage = temp_tenant_storage.get_studio_storage_usage("empty-studio")
        
        assert usage == 0

    def test_check_storage_quota_within_limit(self, temp_tenant_storage, sample_image):
        """Test quota check when within limit."""
        studio_id = "studio-123"
        
        temp_tenant_storage.save_photo(
            file=sample_image,
            studio_id=studio_id,
            project_id=1,
            original_filename="small.jpg",
            generate_variants=False
        )
        
        within_quota, used, max_bytes = temp_tenant_storage.check_storage_quota(studio_id, max_gb=1)
        
        assert within_quota is True
        assert used > 0
        assert max_bytes == 1 * 1024 * 1024 * 1024

    def test_get_storage_stats(self, temp_tenant_storage, sample_image, sample_file):
        """Test getting detailed storage statistics."""
        studio_id = "studio-123"
        
        # Add photo
        temp_tenant_storage.save_photo(
            file=sample_image,
            studio_id=studio_id,
            project_id=1,
            original_filename="photo.jpg",
            generate_variants=True
        )
        
        # Add logo
        temp_tenant_storage.save_logo(
            file=sample_file,
            studio_id=studio_id,
            original_filename="logo.png"
        )
        
        stats = temp_tenant_storage.get_storage_stats(studio_id)
        
        assert stats["total_bytes"] > 0
        assert stats["photo_count"] >= 1  # original + thumbnail
        assert stats["logo_count"] == 1
        assert "total_mb" in stats
        assert "total_gb" in stats


class TestGetStorageService:
    """Test storage factory function."""

    def test_get_local_storage(self):
        """Test getting local storage service."""
        service = get_storage_service(use_s3=False)
        
        assert isinstance(service, LocalStorageService)

    def test_get_s3_storage_returns_s3_service(self):
        """Test getting S3 storage service type."""
        from app.services.storage_service import S3StorageService
        
        service = get_storage_service(use_s3=True)
        
        assert isinstance(service, S3StorageService)
