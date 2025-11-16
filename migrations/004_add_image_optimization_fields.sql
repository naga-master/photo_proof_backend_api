-- Migration: Add Image Optimization Fields
-- Date: 2025-11-16
-- Description: Add variants_json and thumbhash columns to photos table for 5-layer optimization system

-- Add variants_json column to store quality variant paths
-- JSON structure: {"thumbnail": "path", "low": "path", "medium": "path", "high": "path", "print": "path"}
ALTER TABLE photos ADD COLUMN variants_json TEXT DEFAULT NULL;

-- Add thumbhash column to store 32x32 blur placeholder hash
-- ThumbHash is a compact representation of a placeholder for blurry image previews
ALTER TABLE photos ADD COLUMN thumbhash TEXT DEFAULT NULL;

-- Add index on thumbhash for faster lookups (optional, but useful for querying)
CREATE INDEX IF NOT EXISTS idx_photos_thumbhash ON photos(thumbhash);

-- Add comments for documentation (SQLite supports comments in migrations)
-- variants_json: JSON object mapping quality levels to file paths
-- thumbhash: Base64-encoded ThumbHash for instant placeholder display
