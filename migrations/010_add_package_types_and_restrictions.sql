-- Migration 010: Add Package Types and Restrictions System
-- This migration adds support for dynamic package types with customizable restrictions

-- ============================================================================
-- 1. Create package_types table
-- ============================================================================
CREATE TABLE IF NOT EXISTS package_types (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    is_predefined BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    attribute_schema JSON NOT NULL,
    created_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for package_types
CREATE INDEX IF NOT EXISTS idx_package_types_name ON package_types(name);
CREATE INDEX IF NOT EXISTS idx_package_types_active ON package_types(is_active);
CREATE INDEX IF NOT EXISTS idx_package_types_predefined ON package_types(is_predefined);

-- ============================================================================
-- 2. Add new columns to service_packages table
-- ============================================================================
ALTER TABLE service_packages 
ADD COLUMN IF NOT EXISTS package_type_id VARCHAR(36) REFERENCES package_types(id) ON DELETE SET NULL;

ALTER TABLE service_packages 
ADD COLUMN IF NOT EXISTS restrictions JSON;

ALTER TABLE service_packages 
ADD COLUMN IF NOT EXISTS deliverables JSON;

ALTER TABLE service_packages 
ADD COLUMN IF NOT EXISTS lifecycle_config JSON;

-- Create index for package_type_id
CREATE INDEX IF NOT EXISTS idx_service_packages_type ON service_packages(package_type_id);

-- ============================================================================
-- 3. Add new columns to projects table
-- ============================================================================
ALTER TABLE projects 
ADD COLUMN IF NOT EXISTS package_snapshot JSON;

ALTER TABLE projects 
ADD COLUMN IF NOT EXISTS usage_stats JSON;

-- ============================================================================
-- 4. Seed predefined package types
-- ============================================================================

-- Wedding Photography Package Type
INSERT INTO package_types (id, name, display_name, description, icon, is_predefined, is_active, attribute_schema, created_at, updated_at)
VALUES (
    'wedding-photography',
    'wedding',
    'Wedding Photography',
    'Comprehensive wedding photography packages with events, album creation, and deliverables',
    'heart',
    TRUE,
    TRUE,
    '{
        "sections": [
            {
                "title": "Basic Information",
                "fields": [
                    {"name": "name", "type": "text", "label": "Package Name", "required": true},
                    {"name": "description", "type": "textarea", "label": "Description", "required": true},
                    {"name": "price", "type": "number", "label": "Price (INR)", "required": true, "min": 0}
                ]
            },
            {
                "title": "Photo & Video Limits",
                "fields": [
                    {"name": "photo_selection_limit", "type": "number", "label": "Max Photos Client Can Select", "required": true, "min": 0},
                    {"name": "video_support_enabled", "type": "toggle", "label": "Video Support", "required": false},
                    {"name": "video_max_gb", "type": "number", "label": "Max Video Storage (GB)", "required": false, "min": 0, "dependency": {"field": "video_support_enabled", "value": true}}
                ]
            },
            {
                "title": "Event Coverage",
                "fields": [
                    {"name": "reception_coverage", "type": "toggle", "label": "Reception Coverage", "required": false},
                    {"name": "wedding_coverage", "type": "toggle", "label": "Wedding Ceremony Coverage", "required": false},
                    {"name": "prewedding_coverage", "type": "toggle", "label": "Pre-Wedding Shoot", "required": false},
                    {"name": "outdoor_coverage", "type": "toggle", "label": "Outdoor Shoot", "required": false}
                ]
            },
            {
                "title": "Photography Types",
                "fields": [
                    {"name": "candid_photo_count", "type": "number", "label": "Candid Photography (count)", "required": false, "min": 0},
                    {"name": "candid_video_count", "type": "number", "label": "Candid Videography (count)", "required": false, "min": 0},
                    {"name": "traditional_photo_count", "type": "number", "label": "Traditional Photography (count)", "required": false, "min": 0},
                    {"name": "traditional_video_count", "type": "number", "label": "Traditional Videography (count)", "required": false, "min": 0}
                ]
            },
            {
                "title": "Deliverables",
                "fields": [
                    {"name": "album_enabled", "type": "toggle", "label": "Album Creation", "required": false},
                    {"name": "album_quality", "type": "select", "label": "Album Quality", "options": [{"label": "Standard", "value": "standard"}, {"label": "Premium", "value": "premium"}, {"label": "Luxury", "value": "luxury"}], "required": false, "dependency": {"field": "album_enabled", "value": true}},
                    {"name": "album_size", "type": "select", "label": "Album Size", "options": [{"label": "10x14", "value": "10x14"}, {"label": "12x15", "value": "12x15"}, {"label": "14x20", "value": "14x20"}], "required": false, "dependency": {"field": "album_enabled", "value": true}},
                    {"name": "album_pages", "type": "number", "label": "Album Pages", "required": false, "min": 20, "max": 200, "dependency": {"field": "album_enabled", "value": true}},
                    {"name": "frame_count", "type": "number", "label": "Framed Photos (count)", "required": false, "min": 0},
                    {"name": "frame_size", "type": "text", "label": "Frame Size", "placeholder": "e.g., 8x10, 12x18", "required": false},
                    {"name": "pendrive_enabled", "type": "toggle", "label": "Pendrive/USB Included", "required": false},
                    {"name": "dvd_enabled", "type": "toggle", "label": "DVD Included", "required": false}
                ]
            },
            {
                "title": "Timeline & Support",
                "fields": [
                    {"name": "editing_period_months", "type": "number", "label": "Editing Period (months from upload)", "required": true, "min": 1},
                    {"name": "retention_years", "type": "number", "label": "Retention Period (years)", "required": true, "min": 1},
                    {"name": "retention_months", "type": "number", "label": "Retention Period (additional months)", "required": false, "min": 0, "max": 11},
                    {"name": "archival_enabled", "type": "toggle", "label": "Auto Archival", "required": false},
                    {"name": "archival_years", "type": "number", "label": "Archive After (years)", "required": false, "dependency": {"field": "archival_enabled", "value": true}},
                    {"name": "archival_months", "type": "number", "label": "Archive After (additional months)", "required": false, "min": 0, "max": 11, "dependency": {"field": "archival_enabled", "value": true}},
                    {"name": "customer_support", "type": "select", "label": "Customer Support", "options": [{"label": "24/7", "value": "24x7"}, {"label": "Business Hours", "value": "business_hours"}, {"label": "On Demand", "value": "on_demand"}], "required": false}
                ]
            },
            {
                "title": "Integrations",
                "fields": [
                    {"name": "whatsapp_integration", "type": "toggle", "label": "WhatsApp Notifications", "required": false}
                ]
            },
            {
                "title": "Features",
                "fields": [
                    {"name": "features", "type": "textarea", "label": "Features (one per line)", "placeholder": "Enter features, one per line", "required": false}
                ]
            }
        ]
    }'::json,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Corporate Photography Package Type
INSERT INTO package_types (id, name, display_name, description, icon, is_predefined, is_active, attribute_schema, created_at, updated_at)
VALUES (
    'corporate-photography',
    'corporate',
    'Corporate Photography',
    'Professional corporate and business photography packages for headshots, team photos, and events',
    'briefcase',
    TRUE,
    TRUE,
    '{
        "sections": [
            {
                "title": "Basic Information",
                "fields": [
                    {"name": "name", "type": "text", "label": "Package Name", "required": true},
                    {"name": "description", "type": "textarea", "label": "Description", "required": true},
                    {"name": "price", "type": "number", "label": "Price (INR)", "required": true, "min": 0}
                ]
            },
            {
                "title": "Session Details",
                "fields": [
                    {"name": "headshot_count", "type": "number", "label": "Number of Headshots/People", "required": true, "min": 1},
                    {"name": "session_hours", "type": "number", "label": "Session Duration (hours)", "required": true, "min": 1},
                    {"name": "photo_selection_limit", "type": "number", "label": "Final Deliverables Count", "required": true, "min": 1},
                    {"name": "turnaround_days", "type": "number", "label": "Turnaround Time (days)", "required": true, "min": 1}
                ]
            },
            {
                "title": "Service Options",
                "fields": [
                    {"name": "retouching_level", "type": "select", "label": "Retouching Level", "options": [{"label": "Basic", "value": "basic"}, {"label": "Professional", "value": "professional"}, {"label": "Advanced", "value": "advanced"}], "required": true},
                    {"name": "background_options", "type": "multi-select", "label": "Background Options", "options": [{"label": "White", "value": "white"}, {"label": "Gray", "value": "gray"}, {"label": "Custom", "value": "custom"}], "required": false},
                    {"name": "high_res_access", "type": "toggle", "label": "High Resolution Files", "required": false},
                    {"name": "team_photo", "type": "toggle", "label": "Team Photo Included", "required": false}
                ]
            },
            {
                "title": "Location & Extras",
                "fields": [
                    {"name": "onsite_enabled", "type": "toggle", "label": "On-site Service", "required": false},
                    {"name": "studio_enabled", "type": "toggle", "label": "Studio Session", "required": false},
                    {"name": "additional_photographers", "type": "number", "label": "Additional Photographers", "required": false, "min": 0}
                ]
            },
            {
                "title": "Usage Rights",
                "fields": [
                    {"name": "usage_rights", "type": "select", "label": "Usage Rights", "options": [{"label": "Internal Only", "value": "internal"}, {"label": "Marketing", "value": "marketing"}, {"label": "Unlimited", "value": "unlimited"}], "required": true}
                ]
            },
            {
                "title": "Timeline",
                "fields": [
                    {"name": "retention_years", "type": "number", "label": "Retention Period (years)", "required": true, "min": 1},
                    {"name": "editing_period_months", "type": "number", "label": "Editing Period (months)", "required": false, "min": 1}
                ]
            },
            {
                "title": "Features",
                "fields": [
                    {"name": "features", "type": "textarea", "label": "Features (one per line)", "required": false}
                ]
            }
        ]
    }'::json,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Event Photography Package Type
INSERT INTO package_types (id, name, display_name, description, icon, is_predefined, is_active, attribute_schema, created_at, updated_at)
VALUES (
    'event-photography',
    'event',
    'Event Photography',
    'Coverage for conferences, parties, corporate events, and gatherings',
    'calendar',
    TRUE,
    TRUE,
    '{
        "sections": [
            {
                "title": "Basic Information",
                "fields": [
                    {"name": "name", "type": "text", "label": "Package Name", "required": true},
                    {"name": "description", "type": "textarea", "label": "Description", "required": true},
                    {"name": "price", "type": "number", "label": "Price (INR)", "required": true, "min": 0}
                ]
            },
            {
                "title": "Coverage Details",
                "fields": [
                    {"name": "coverage_hours", "type": "number", "label": "Coverage Hours", "required": true, "min": 1},
                    {"name": "photographer_count", "type": "number", "label": "Number of Photographers", "required": true, "min": 1},
                    {"name": "photo_selection_limit", "type": "number", "label": "Max Deliverable Photos", "required": true, "min": 1}
                ]
            },
            {
                "title": "Video & Extras",
                "fields": [
                    {"name": "video_highlights", "type": "toggle", "label": "Video Highlights", "required": false},
                    {"name": "video_duration_minutes", "type": "number", "label": "Highlight Duration (minutes)", "required": false, "dependency": {"field": "video_highlights", "value": true}},
                    {"name": "drone_coverage", "type": "toggle", "label": "Drone Coverage", "required": false},
                    {"name": "live_streaming", "type": "toggle", "label": "Live Streaming", "required": false},
                    {"name": "same_day_preview", "type": "toggle", "label": "Same-Day Preview", "required": false},
                    {"name": "photo_booth", "type": "toggle", "label": "Photo Booth", "required": false}
                ]
            },
            {
                "title": "Delivery",
                "fields": [
                    {"name": "online_gallery_months", "type": "number", "label": "Online Gallery Duration (months)", "required": true, "min": 1},
                    {"name": "retention_years", "type": "number", "label": "Retention Period (years)", "required": true, "min": 1}
                ]
            },
            {
                "title": "Features",
                "fields": [
                    {"name": "features", "type": "textarea", "label": "Features (one per line)", "required": false}
                ]
            }
        ]
    }'::json,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Maternity & Newborn Package Type
INSERT INTO package_types (id, name, display_name, description, icon, is_predefined, is_active, attribute_schema, created_at, updated_at)
VALUES (
    'maternity-newborn',
    'maternity',
    'Maternity & Newborn',
    'Specialized packages for pregnancy and newborn photography',
    'baby',
    TRUE,
    TRUE,
    '{
        "sections": [
            {
                "title": "Basic Information",
                "fields": [
                    {"name": "name", "type": "text", "label": "Package Name", "required": true},
                    {"name": "description", "type": "textarea", "label": "Description", "required": true},
                    {"name": "price", "type": "number", "label": "Price (INR)", "required": true, "min": 0}
                ]
            },
            {
                "title": "Session Details",
                "fields": [
                    {"name": "maternity_sessions", "type": "number", "label": "Maternity Sessions", "required": false, "min": 0},
                    {"name": "newborn_sessions", "type": "number", "label": "Newborn Sessions", "required": false, "min": 0},
                    {"name": "session_hours", "type": "number", "label": "Session Duration (hours)", "required": true, "min": 1},
                    {"name": "photo_selection_limit", "type": "number", "label": "Final Deliverable Photos", "required": true, "min": 1}
                ]
            },
            {
                "title": "Services Included",
                "fields": [
                    {"name": "wardrobe_access", "type": "toggle", "label": "Wardrobe Access", "required": false},
                    {"name": "props_included", "type": "toggle", "label": "Props Included", "required": false},
                    {"name": "family_photos", "type": "toggle", "label": "Family Photos", "required": false},
                    {"name": "milestone_sessions", "type": "toggle", "label": "Milestone Sessions (3m, 6m, 12m)", "required": false}
                ]
            },
            {
                "title": "Deliverables",
                "fields": [
                    {"name": "print_count", "type": "number", "label": "Print Inclusions (count)", "required": false, "min": 0},
                    {"name": "print_sizes", "type": "text", "label": "Print Sizes", "placeholder": "e.g., 8x10, 11x14", "required": false},
                    {"name": "album_enabled", "type": "toggle", "label": "Album Included", "required": false},
                    {"name": "digital_files_all", "type": "toggle", "label": "All Digital Files", "required": false}
                ]
            },
            {
                "title": "Timeline",
                "fields": [
                    {"name": "retention_years", "type": "number", "label": "Retention Period (years)", "required": true, "min": 1}
                ]
            },
            {
                "title": "Features",
                "fields": [
                    {"name": "features", "type": "textarea", "label": "Features (one per line)", "required": false}
                ]
            }
        ]
    }'::json,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Product Photography Package Type
INSERT INTO package_types (id, name, display_name, description, icon, is_predefined, is_active, attribute_schema, created_at, updated_at)
VALUES (
    'product-photography',
    'product',
    'Product Photography',
    'E-commerce and product photography for online stores and catalogs',
    'shopping-bag',
    TRUE,
    TRUE,
    '{
        "sections": [
            {
                "title": "Basic Information",
                "fields": [
                    {"name": "name", "type": "text", "label": "Package Name", "required": true},
                    {"name": "description", "type": "textarea", "label": "Description", "required": true},
                    {"name": "price", "type": "number", "label": "Price (INR)", "required": true, "min": 0}
                ]
            },
            {
                "title": "Product Details",
                "fields": [
                    {"name": "product_count", "type": "number", "label": "Number of Products", "required": true, "min": 1},
                    {"name": "images_per_product", "type": "number", "label": "Images Per Product", "required": true, "min": 1},
                    {"name": "photo_selection_limit", "type": "number", "label": "Total Deliverable Images", "required": true, "min": 1}
                ]
            },
            {
                "title": "Style & Background",
                "fields": [
                    {"name": "background_type", "type": "multi-select", "label": "Background Types", "options": [{"label": "White", "value": "white"}, {"label": "Lifestyle", "value": "lifestyle"}, {"label": "Custom", "value": "custom"}], "required": true},
                    {"name": "retouching_level", "type": "select", "label": "Retouching Level", "options": [{"label": "Basic", "value": "basic"}, {"label": "Advanced", "value": "advanced"}], "required": true},
                    {"name": "three_sixty_view", "type": "toggle", "label": "360° View", "required": false},
                    {"name": "model_mannequin", "type": "toggle", "label": "Model/Mannequin", "required": false}
                ]
            },
            {
                "title": "Delivery",
                "fields": [
                    {"name": "file_formats", "type": "multi-select", "label": "File Formats", "options": [{"label": "JPG", "value": "jpg"}, {"label": "PNG", "value": "png"}, {"label": "RAW", "value": "raw"}], "required": true},
                    {"name": "turnaround_days", "type": "number", "label": "Turnaround Time (days)", "required": true, "min": 1},
                    {"name": "revision_rounds", "type": "number", "label": "Revision Rounds", "required": false, "min": 0}
                ]
            },
            {
                "title": "Usage Rights",
                "fields": [
                    {"name": "usage_rights", "type": "select", "label": "Usage Rights", "options": [{"label": "E-commerce Only", "value": "ecommerce"}, {"label": "Marketing", "value": "marketing"}, {"label": "All", "value": "all"}], "required": true}
                ]
            },
            {
                "title": "Features",
                "fields": [
                    {"name": "features", "type": "textarea", "label": "Features (one per line)", "required": false}
                ]
            }
        ]
    }'::json,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Portrait Photography Package Type
INSERT INTO package_types (id, name, display_name, description, icon, is_predefined, is_active, attribute_schema, created_at, updated_at)
VALUES (
    'portrait-photography',
    'portrait',
    'Portrait Photography',
    'Individual and family portrait photography packages',
    'user',
    TRUE,
    TRUE,
    '{
        "sections": [
            {
                "title": "Basic Information",
                "fields": [
                    {"name": "name", "type": "text", "label": "Package Name", "required": true},
                    {"name": "description", "type": "textarea", "label": "Description", "required": true},
                    {"name": "price", "type": "number", "label": "Price (INR)", "required": true, "min": 0}
                ]
            },
            {
                "title": "Session Details",
                "fields": [
                    {"name": "session_hours", "type": "number", "label": "Session Duration (hours)", "required": true, "min": 1},
                    {"name": "photo_selection_limit", "type": "number", "label": "Final Deliverable Photos", "required": true, "min": 1},
                    {"name": "outfit_changes", "type": "number", "label": "Outfit Changes", "required": false, "min": 0},
                    {"name": "backdrop_options", "type": "number", "label": "Backdrop Options", "required": false, "min": 1}
                ]
            },
            {
                "title": "Location",
                "fields": [
                    {"name": "studio_session", "type": "toggle", "label": "Studio Session", "required": false},
                    {"name": "outdoor_session", "type": "toggle", "label": "Outdoor Session", "required": false},
                    {"name": "home_session", "type": "toggle", "label": "Home Session", "required": false}
                ]
            },
            {
                "title": "Deliverables",
                "fields": [
                    {"name": "print_count", "type": "number", "label": "Print Inclusions (count)", "required": false, "min": 0},
                    {"name": "print_sizes", "type": "text", "label": "Print Sizes", "placeholder": "e.g., 8x10, 11x14", "required": false},
                    {"name": "album_enabled", "type": "toggle", "label": "Album Included", "required": false},
                    {"name": "digital_files", "type": "select", "label": "Digital Files", "options": [{"label": "All Files", "value": "all"}, {"label": "Selected Only", "value": "selected"}], "required": true},
                    {"name": "retouching", "type": "select", "label": "Retouching Level", "options": [{"label": "Basic", "value": "basic"}, {"label": "Professional", "value": "professional"}], "required": true}
                ]
            },
            {
                "title": "Timeline",
                "fields": [
                    {"name": "retention_years", "type": "number", "label": "Retention Period (years)", "required": true, "min": 1}
                ]
            },
            {
                "title": "Features",
                "fields": [
                    {"name": "features", "type": "textarea", "label": "Features (one per line)", "required": false}
                ]
            }
        ]
    }'::json,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- ============================================================================
-- 5. Create default "Custom" package type for backward compatibility
-- ============================================================================
INSERT INTO package_types (id, name, display_name, description, icon, is_predefined, is_active, attribute_schema, created_at, updated_at)
VALUES (
    'custom-package',
    'custom',
    'Custom Package',
    'Custom package type for existing packages without specific type',
    'star',
    FALSE,
    TRUE,
    '{
        "sections": [
            {
                "title": "Basic Information",
                "fields": [
                    {"name": "name", "type": "text", "label": "Package Name", "required": true},
                    {"name": "description", "type": "textarea", "label": "Description", "required": true},
                    {"name": "price", "type": "number", "label": "Price (INR)", "required": true, "min": 0}
                ]
            },
            {
                "title": "Features",
                "fields": [
                    {"name": "features", "type": "textarea", "label": "Features (one per line)", "required": false}
                ]
            }
        ]
    }'::json,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- ============================================================================
-- 6. Backfill existing service_packages with custom type
-- ============================================================================
UPDATE service_packages 
SET package_type_id = 'custom-package'
WHERE package_type_id IS NULL;

-- ============================================================================
-- 7. Set default empty JSON for new columns
-- ============================================================================
UPDATE service_packages 
SET restrictions = '{}'::json
WHERE restrictions IS NULL;

UPDATE service_packages 
SET deliverables = '[]'::json
WHERE deliverables IS NULL;

UPDATE service_packages 
SET lifecycle_config = '{}'::json
WHERE lifecycle_config IS NULL;

UPDATE projects 
SET package_snapshot = '{}'::json
WHERE package_snapshot IS NULL;

UPDATE projects 
SET usage_stats = '{"photos_selected": 0, "video_gb_used": 0}'::json
WHERE usage_stats IS NULL;

-- ============================================================================
-- 8. Comments for documentation
-- ============================================================================
COMMENT ON TABLE package_types IS 'Defines different types of photography packages with dynamic form schemas';
COMMENT ON COLUMN package_types.attribute_schema IS 'JSON schema defining the form fields for this package type';
COMMENT ON COLUMN service_packages.restrictions IS 'JSON storing package-specific restrictions (photo limits, video limits, etc.)';
COMMENT ON COLUMN service_packages.lifecycle_config IS 'JSON storing retention, archival, and editing period configurations';
COMMENT ON COLUMN projects.package_snapshot IS 'Frozen copy of package configuration at project creation time';
COMMENT ON COLUMN projects.usage_stats IS 'Tracks actual usage against package limits';
