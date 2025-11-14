"""Version management service for photo editing workflow."""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from PIL import Image
import io

from app.db.models.photo import Photo, PhotoVersion
from app.db.models.project import Project
from app.services.storage_service import StorageService
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class VersionService:
    """Service for managing photo versions and filename matching."""
    
    def __init__(self, db: Session, storage: StorageService):
        self.db = db
        self.storage = storage
    
    async def create_version(
        self,
        photo_id: int,
        file_data: bytes,
        filename: str,
        uploaded_by: str,
        version_label: Optional[str] = None,
        upload_note: Optional[str] = None
    ) -> PhotoVersion:
        """
        Create new version for existing photo.
        
        Args:
            photo_id: ID of photo to version
            file_data: Binary file data
            filename: Original filename of edited photo
            uploaded_by: User ID of uploader
            version_label: Optional custom label (e.g., "Final", "Color Corrected")
            upload_note: Optional note about this version
            
        Returns:
            Created PhotoVersion record
            
        Raises:
            ValueError: If photo not found or version limit reached
        """
        # Get photo and validate
        photo = self.db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise ValueError(f"Photo {photo_id} not found")
        
        # Check version count limit
        if photo.version_count >= settings.max_photo_versions:
            raise ValueError(f"Photo {photo_id} has reached maximum version limit ({settings.max_photo_versions})")
        
        # Calculate next version number
        next_version_number = photo.version_count + 1
        
        # Extract image dimensions
        try:
            image_buffer = io.BytesIO(file_data)
            image = Image.open(image_buffer)
            image.verify()
            image_buffer.seek(0)
            image = Image.open(image_buffer)
            width, height = image.size
            mime_type = Image.MIME.get(image.format, 'image/jpeg')
        except Exception as e:
            logger.warning(f"Could not extract dimensions for {filename}: {e}")
            width, height = 1920, 1080
            mime_type = 'image/jpeg'
        
        # Create storage path
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = filename.replace(" ", "_")
        storage_path = f"projects/{photo.project_id}/photos/{photo_id}/v{next_version_number}_{timestamp}_{safe_filename}"
        
        # Save file to storage
        file_obj = io.BytesIO(file_data)
        url = await self.storage.save_file(file_obj, storage_path)
        
        # Create PhotoVersion record
        photo_version = PhotoVersion(
            photo_id=photo_id,
            version_number=next_version_number,
            src=url,
            storage_path=storage_path,
            thumbnail_path=None,  # TODO: Generate thumbnail
            preview_path=None,
            original_filename=filename,
            file_size=len(file_data),
            mime_type=mime_type,
            width=width,
            height=height,
            is_original=False,
            version_label=version_label,
            replaced_version_id=photo.current_version_id,  # Track which version this replaces
            uploaded_by=uploaded_by,
            upload_note=upload_note,
        )
        
        self.db.add(photo_version)
        self.db.flush()
        
        # Update photo to point to new version
        photo.current_version_id = photo_version.id
        photo.version_count = next_version_number
        photo.last_version_updated_at = datetime.utcnow()
        
        # Update photo.src to point to new version for backwards compatibility
        photo.src = url
        photo.storage_path = storage_path
        photo.width = width
        photo.height = height
        photo.file_size = len(file_data)
        photo.mime_type = mime_type
        
        self.db.commit()
        self.db.refresh(photo_version)
        
        logger.info(f"Created version {next_version_number} for photo {photo_id}", extra={
            "photo_id": photo_id,
            "version_number": next_version_number,
            "version_label": version_label,
            "file_size": len(file_data)
        })
        
        return photo_version
    
    def get_version_history(self, photo_id: int) -> List[PhotoVersion]:
        """
        Get all versions for a photo, sorted by version_number desc (latest first).
        
        Args:
            photo_id: ID of photo
            
        Returns:
            List of PhotoVersion records
        """
        versions = (
            self.db.query(PhotoVersion)
            .filter(PhotoVersion.photo_id == photo_id)
            .order_by(PhotoVersion.version_number.desc())
            .all()
        )
        return versions
    
    def set_current_version(self, photo_id: int, version_id: int) -> Photo:
        """
        Change which version is currently active (revert to older version).
        
        Args:
            photo_id: ID of photo
            version_id: ID of version to set as current
            
        Returns:
            Updated Photo record
            
        Raises:
            ValueError: If photo or version not found, or version doesn't belong to photo
        """
        photo = self.db.query(Photo).filter(Photo.id == photo_id).first()
        if not photo:
            raise ValueError(f"Photo {photo_id} not found")
        
        version = self.db.query(PhotoVersion).filter(PhotoVersion.id == version_id).first()
        if not version:
            raise ValueError(f"Version {version_id} not found")
        
        if version.photo_id != photo_id:
            raise ValueError(f"Version {version_id} does not belong to photo {photo_id}")
        
        # Update photo to point to selected version
        photo.current_version_id = version_id
        photo.last_version_updated_at = datetime.utcnow()
        
        # Update photo.src for backwards compatibility
        photo.src = version.src
        photo.storage_path = version.storage_path
        photo.width = version.width
        photo.height = version.height
        photo.file_size = version.file_size
        photo.mime_type = version.mime_type
        
        self.db.commit()
        self.db.refresh(photo)
        
        logger.info(f"Set version {version.version_number} as current for photo {photo_id}")
        
        return photo
    
    def match_filenames(
        self,
        edited_filenames: List[str],
        original_photos: List[Photo],
        confidence_threshold: float = None
    ) -> Dict[str, Any]:
        """
        Smart filename matching algorithm.
        Matches edited filenames to original photos using multiple strategies.
        
        Args:
            edited_filenames: List of edited photo filenames to match
            original_photos: List of Photo records from project
            confidence_threshold: Minimum confidence for auto-match (default from config)
            
        Returns:
            Dictionary with 'matched' and 'unmatched' lists:
            {
                "matched": [
                    {
                        "edited_filename": str,
                        "photo_id": int,
                        "original_filename": str,
                        "confidence": float (0.0-1.0),
                        "match_reason": str
                    }
                ],
                "unmatched": [
                    {
                        "edited_filename": str,
                        "suggestions": [
                            {"photo_id": int, "filename": str, "confidence": float}
                        ]
                    }
                ]
            }
        """
        if confidence_threshold is None:
            confidence_threshold = settings.min_match_confidence
        
        matched = []
        unmatched = []
        
        # Create lookup for faster searching
        photos_by_filename = {
            self._normalize_filename(photo.original_filename): photo
            for photo in original_photos
        }
        
        for edited_filename in edited_filenames:
            edited_normalized = self._normalize_filename(edited_filename)
            edited_base = self._get_basename(edited_filename)
            
            best_match = None
            confidence = 0.0
            match_reason = ""
            
            # Priority 1: Exact match (100%)
            if edited_normalized in photos_by_filename:
                best_match = photos_by_filename[edited_normalized]
                confidence = 1.0
                match_reason = "exact"
            
            # Priority 2: Suffix patterns (95%)
            if not best_match:
                suffix_patterns = [
                    r'_edited$', r'_edit$', r'-edited$', r'-edit$',
                    r'_final$', r'-final$', r' edited$', r' edit$',
                    r'_v\d+$', r'-v\d+$', r' \(\d+\)$',
                    r'_corrected$', r'-corrected$', r'_retouched$'
                ]
                
                for pattern in suffix_patterns:
                    clean_base = re.sub(pattern, '', edited_base, flags=re.IGNORECASE)
                    clean_normalized = self._normalize_filename(clean_base + self._get_extension(edited_filename))
                    
                    if clean_normalized in photos_by_filename:
                        best_match = photos_by_filename[clean_normalized]
                        confidence = 0.95
                        match_reason = "suffix_pattern"
                        break
            
            # Priority 3: Extension-agnostic match (85%)
            if not best_match:
                for orig_filename, photo in photos_by_filename.items():
                    orig_base = self._get_basename(photo.original_filename)
                    if self._normalize_filename(orig_base) == self._normalize_filename(edited_base):
                        best_match = photo
                        confidence = 0.85
                        match_reason = "extension_difference"
                        break
            
            # If we found a high-confidence match
            if best_match and confidence >= confidence_threshold:
                matched.append({
                    "edited_filename": edited_filename,
                    "photo_id": best_match.id,
                    "original_filename": best_match.original_filename,
                    "confidence": confidence,
                    "match_reason": match_reason
                })
            else:
                # Generate suggestions for manual mapping
                suggestions = self._generate_suggestions(edited_filename, original_photos, max_suggestions=5)
                unmatched.append({
                    "edited_filename": edited_filename,
                    "suggestions": suggestions
                })
        
        logger.info(f"Filename matching complete", extra={
            "total": len(edited_filenames),
            "matched": len(matched),
            "unmatched": len(unmatched)
        })
        
        return {
            "matched": matched,
            "unmatched": unmatched
        }
    
    def _normalize_filename(self, filename: str) -> str:
        """Normalize filename for comparison (lowercase, strip whitespace)."""
        return filename.lower().strip()
    
    def _get_basename(self, filename: str) -> str:
        """Get filename without extension."""
        if '.' in filename:
            return '.'.join(filename.split('.')[:-1])
        return filename
    
    def _get_extension(self, filename: str) -> str:
        """Get file extension including dot."""
        if '.' in filename:
            return '.' + filename.split('.')[-1]
        return ''
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings using Levenshtein distance.
        Returns float between 0.0 (no similarity) and 1.0 (identical).
        """
        str1 = str1.lower()
        str2 = str2.lower()
        
        # Quick check for identical strings
        if str1 == str2:
            return 1.0
        
        # Check for substring match
        if str1 in str2 or str2 in str1:
            shorter = min(len(str1), len(str2))
            longer = max(len(str1), len(str2))
            return shorter / longer
        
        # Levenshtein distance calculation
        if len(str1) < len(str2):
            str1, str2 = str2, str1
        
        distances = range(len(str2) + 1)
        for i1, char1 in enumerate(str1):
            distances_ = [i1 + 1]
            for i2, char2 in enumerate(str2):
                if char1 == char2:
                    distances_.append(distances[i2])
                else:
                    distances_.append(1 + min((distances[i2], distances[i2 + 1], distances_[-1])))
            distances = distances_
        
        max_len = max(len(str1), len(str2))
        if max_len == 0:
            return 1.0
        
        return 1.0 - (distances[-1] / max_len)
    
    def _generate_suggestions(
        self,
        edited_filename: str,
        original_photos: List[Photo],
        max_suggestions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate filename match suggestions for manual mapping.
        
        Args:
            edited_filename: Filename to find suggestions for
            original_photos: List of original photos
            max_suggestions: Maximum number of suggestions to return
            
        Returns:
            List of suggestions sorted by confidence
        """
        edited_base = self._get_basename(edited_filename)
        suggestions = []
        
        for photo in original_photos:
            orig_base = self._get_basename(photo.original_filename)
            similarity = self._calculate_similarity(edited_base, orig_base)
            
            if similarity > 0.3:  # Minimum threshold for suggestions
                suggestions.append({
                    "photo_id": photo.id,
                    "filename": photo.original_filename,
                    "confidence": round(similarity, 2)
                })
        
        # Sort by confidence and limit
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        return suggestions[:max_suggestions]
