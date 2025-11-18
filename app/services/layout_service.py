"""Layout service for gallery customization and branding."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.schemas.layouts import (
    LayoutTemplate,
    LayoutSettings,
    LayoutPreview,
    BrandingConfig,
    LayoutRequest,
    LayoutResponse,
    CustomLayoutRequest
)


class LayoutService:
    """Service for managing gallery layouts and customization."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_available_templates(self, category: Optional[str] = None) -> List[LayoutTemplate]:
        """Get all available layout templates."""
        # Mock templates - in production, these would come from the database
        templates = [
            LayoutTemplate(
                id="grid-classic",
                name="Classic Grid",
                description="Clean, organized grid layout perfect for portfolios",
                category="grid",
                preview_url="/templates/grid-classic-preview.jpg",
                settings_schema={
                    "columns": {"type": "number", "min": 2, "max": 6, "default": 3},
                    "spacing": {"type": "number", "min": 0, "max": 50, "default": 10},
                    "aspect_ratio": {"type": "select", "options": ["auto", "1:1", "4:3", "16:9"], "default": "auto"}
                },
                is_premium=False,
                created_at=datetime.utcnow()
            ),
            LayoutTemplate(
                id="masonry-modern",
                name="Modern Masonry",
                description="Dynamic masonry layout with natural image proportions",
                category="masonry",
                preview_url="/templates/masonry-modern-preview.jpg",
                settings_schema={
                    "columns": {"type": "number", "min": 2, "max": 5, "default": 3},
                    "gutter": {"type": "number", "min": 5, "max": 30, "default": 15},
                    "show_captions": {"type": "boolean", "default": True}
                },
                is_premium=True,
                created_at=datetime.utcnow()
            ),
            LayoutTemplate(
                id="slideshow-elegant",
                name="Elegant Slideshow",
                description="Full-screen slideshow with elegant transitions",
                category="slideshow",
                preview_url="/templates/slideshow-elegant-preview.jpg",
                settings_schema={
                    "autoplay": {"type": "boolean", "default": False},
                    "transition": {"type": "select", "options": ["fade", "slide", "zoom"], "default": "fade"},
                    "show_thumbnails": {"type": "boolean", "default": True},
                    "show_controls": {"type": "boolean", "default": True}
                },
                is_premium=True,
                created_at=datetime.utcnow()
            )
        ]
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        return templates
    
    def create_custom_layout(
        self, 
        studio_id: str, 
        request: CustomLayoutRequest
    ) -> LayoutTemplate:
        """Create a custom layout template."""
        # Mock implementation
        custom_template = LayoutTemplate(
            id=f"custom-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            name=request.name,
            description=request.description,
            category="custom",
            preview_url="/templates/custom-preview.jpg",
            settings_schema=request.settings_schema,
            is_premium=False,
            is_custom=True,
            studio_id=studio_id,
            created_at=datetime.utcnow()
        )
        
        return custom_template
    
    def apply_layout(
        self, 
        project_id: str, 
        template_id: str, 
        settings: Dict[str, Any]
    ) -> LayoutResponse:
        """Apply a layout template to a project."""
        # Mock implementation
        layout_response = LayoutResponse(
            project_id=project_id,
            template_id=template_id,
            settings=settings,
            preview_url=f"/previews/project-{project_id}-layout.jpg",
            applied_at=datetime.utcnow(),
            status="applied"
        )
        
        return layout_response
    
    def get_branding_config(self, studio_id: str) -> BrandingConfig:
        """Get studio branding configuration."""
        # Mock branding config
        return BrandingConfig(
            studio_id=studio_id,
            logo_url="/branding/studio-logo.png",
            primary_color="#1f2937",
            secondary_color="#f3f4f6",
            accent_color="#3b82f6",
            font_family="Inter",
            show_logo=True,
            show_studio_name=True,
            custom_css="",
            watermark_enabled=False,
            watermark_position="bottom-right",
            watermark_opacity=0.7,
            updated_at=datetime.utcnow()
        )
    
    def update_branding(
        self, 
        studio_id: str, 
        branding: Dict[str, Any]
    ) -> BrandingConfig:
        """Update studio branding configuration."""
        # Mock implementation
        updated_branding = BrandingConfig(
            studio_id=studio_id,
            **branding,
            updated_at=datetime.utcnow()
        )
        
        return updated_branding
    
    def generate_preview(
        self, 
        template_id: str, 
        settings: Dict[str, Any],
        sample_images: Optional[List[str]] = None
    ) -> LayoutPreview:
        """Generate a preview of the layout with given settings."""
        # Mock preview generation
        preview = LayoutPreview(
            template_id=template_id,
            settings=settings,
            preview_url=f"/previews/layout-{template_id}-preview.jpg",
            mobile_preview_url=f"/previews/layout-{template_id}-mobile-preview.jpg",
            generated_at=datetime.utcnow(),
            expires_at=datetime.utcnow().replace(hour=23, minute=59, second=59)
        )
        
        return preview
    
    def get_layout_analytics(self, studio_id: str) -> Dict[str, Any]:
        """Get analytics on layout usage and performance."""
        # Mock analytics
        return {
            "most_used_templates": [
                {"template_id": "grid-classic", "usage_count": 45, "percentage": 52.3},
                {"template_id": "masonry-modern", "usage_count": 28, "percentage": 32.6},
                {"template_id": "slideshow-elegant", "usage_count": 13, "percentage": 15.1}
            ],
            "avg_engagement_by_layout": [
                {"template_id": "slideshow-elegant", "avg_session_duration": 420},
                {"template_id": "masonry-modern", "avg_session_duration": 385},
                {"template_id": "grid-classic", "avg_session_duration": 340}
            ],
            "conversion_rates": [
                {"template_id": "slideshow-elegant", "conversion_rate": 23.4},
                {"template_id": "masonry-modern", "conversion_rate": 19.8},
                {"template_id": "grid-classic", "conversion_rate": 16.2}
            ],
            "mobile_performance": {
                "mobile_friendly_score": 94,
                "mobile_bounce_rate": 12.3,
                "mobile_conversion_rate": 18.7
            }
        }