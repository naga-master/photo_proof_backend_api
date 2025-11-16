"""
Image Processing Service

Server-side image processing for quality variants and optimization.
"""

import json
import io
from pathlib import Path
from typing import Dict, Optional
from PIL import Image, ImageOps
from sqlalchemy.orm import Session

from app.db.models import Photo


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
        self.variants_dir = Path("uploads/variants")
        self.variants_dir.mkdir(parents=True, exist_ok=True)
    
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
        print(f"[ImageProcessing] Generating variants for photo {photo.id}")
        
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
                        photo.id,
                        variant_name,
                        settings['width'],
                        settings['quality']
                    )
                    variants[variant_name] = variant_path
                    print(f"[ImageProcessing] Created {variant_name} variant: {variant_path}")
            
            # Store variants in photo record
            photo.variants_json = json.dumps(variants)
            db.commit()
            
            print(f"[ImageProcessing] All variants generated for photo {photo.id}")
            return variants
            
        except Exception as e:
            print(f"[ImageProcessing] Error generating variants: {e}")
            raise
    
    async def create_variant(
        self,
        img: Image.Image,
        photo_id: int,
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
        
        # Create output path
        variant_filename = f"{photo_id}_{variant_name}.webp"
        variant_path = self.variants_dir / variant_filename
        
        # Save as WebP
        resized.save(
            variant_path,
            'WEBP',
            quality=quality,
            method=6  # Slowest but best compression
        )
        
        # Return relative path for URL construction
        return f"uploads/variants/{variant_filename}"
    
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
            print(f"[ImageProcessing] Error generating ThumbHash: {e}")
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
