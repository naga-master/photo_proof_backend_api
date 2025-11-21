"""
Image Processing Service

Server-side image processing for quality variants and optimization.
"""

import json
import io
import logging
from pathlib import Path
from typing import Dict, Optional
from PIL import Image, ImageOps
from sqlalchemy.orm import Session

from app.db.models import Photo


logger = logging.getLogger(__name__)


class ImageProcessingService:
    """Service for server-side image processing"""
    
    # Quality variant definitions
    VARIANTS = {
        'thumbnail': {'width': 200, 'quality': 60},
        'low': {'width': 800, 'quality': 70},
        'medium': {'width': 1920, 'quality': 80},
        'high': {'width': 3840, 'quality': 90},
        'print': {'width': None, 'quality': 95},  # Original size
    }
    
    def __init__(self):
        self.uploads_base = Path("uploads")
        self.uploads_base.mkdir(parents=True, exist_ok=True)
    
    def get_project_variants_dir(self, project_id: int, photo_id: int) -> Path:
        """Get variants directory for a specific photo in a project"""
        variants_dir = self.uploads_base / "projects" / str(project_id) / "variants" / str(photo_id)
        variants_dir.mkdir(parents=True, exist_ok=True)
        return variants_dir
    
    async def generate_quality_variants(
        self,
        db: Session,
        photo: Photo,
        original_file_path: Path
    ) -> Dict[str, str]:
        """
        Generate all quality variants for a photo.
        Returns dict mapping quality names to file paths.
        """
        logger.debug(f"[ImageProcessing] Generating variants for photo {photo.id}")
        
        variants = {}
        
        try:
            # Open original image
            with Image.open(original_file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Generate each variant
                for variant_name, settings in self.VARIANTS.items():
                    variant_path = await self.create_variant(
                        img,
                        photo,
                        variant_name,
                        settings['width'],
                        settings['quality']
                    )
                    variants[variant_name] = variant_path
                    logger.debug(f"[ImageProcessing] Created {variant_name} variant: {variant_path}")
            
            # Store variants in photo record
            photo.variants_json = json.dumps(variants)
            db.commit()
            
            logger.debug(f"[ImageProcessing] All variants generated for photo {photo.id}")
            return variants
            
        except Exception as e:
            logger.debug(f"[ImageProcessing] Error generating variants: {e}")
            raise
    
    async def create_variant(
        self,
        img: Image.Image,
        photo: Photo,
        variant_name: str,
        target_width: Optional[int],
        quality: int
    ) -> str:
        """Create a single quality variant"""
        
        # Resize if needed
        if target_width and img.width > target_width:
            # Calculate new dimensions maintaining aspect ratio
            ratio = target_width / img.width
            new_height = int(img.height * ratio)
            resized = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
        else:
            resized = img
        
        # Auto-orient based on EXIF
        resized = ImageOps.exif_transpose(resized)
        
        # Get project-scoped variants directory
        variants_dir = self.get_project_variants_dir(photo.project_id, photo.id)
        
        # Simple filename (no photo ID prefix needed - already in directory structure)
        variant_filename = f"{variant_name}.webp"
        variant_path = variants_dir / variant_filename
        
        # Save as WebP
        resized.save(
            variant_path,
            'WEBP',
            quality=quality,
            method=6  # Slowest but best compression
        )
        
        # Return relative path from uploads/
        return f"projects/{photo.project_id}/variants/{photo.id}/{variant_filename}"
    
    async def generate_thumbhash(
        self,
        original_file_path: Path
    ) -> str:
        """
        Generate ThumbHash for a photo.
        Returns base64-encoded ThumbHash string.
        """
        try:
            with Image.open(original_file_path) as img:
                # Resize to 32x32 for ThumbHash
                thumb = img.resize((32, 32), Image.Resampling.LANCZOS)
                
                # Convert to RGB
                if thumb.mode != 'RGB':
                    thumb = thumb.convert('RGB')
                
                # Get pixel data
                pixels = thumb.tobytes()
                
                # For now, return a placeholder
                # In production, use actual ThumbHash library
                import base64
                import hashlib
                hash_bytes = hashlib.sha256(pixels).digest()[:10]
                return base64.b64encode(hash_bytes).decode('ascii')
                
        except Exception as e:
            logger.debug(f"[ImageProcessing] Error generating ThumbHash: {e}")
            return ""
    
    def get_variant_path(
        self,
        photo: Photo,
        quality: str
    ) -> Optional[str]:
        """Get the file path for a specific quality variant"""
        if not photo.variants_json:
            return None
        
        try:
            variants = json.loads(photo.variants_json)
            return variants.get(quality)
        except (json.JSONDecodeError, AttributeError):
            return None
    
    async def regenerate_variants_if_needed(
        self,
        db: Session,
        photo: Photo,
        original_file_path: Path
    ) -> bool:
        """
        Regenerate variants if they don't exist or are outdated.
        Returns True if regenerated, False if already up-to-date.
        """
        # Check if variants exist
        if photo.variants_json:
            try:
                variants = json.loads(photo.variants_json)
                # Check if all variant files exist
                all_exist = all(
                    Path(variant_path).exists()
                    for variant_path in variants.values()
                )
                if all_exist:
                    return False  # Already up-to-date
            except (json.JSONDecodeError, AttributeError):
                pass
        
        # Regenerate variants
        await self.generate_quality_variants(db, photo, original_file_path)
        return True
