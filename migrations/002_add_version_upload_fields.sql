-- Migration: Add version upload fields to upload_tokens table
-- Date: 2025-11-15
-- Purpose: Enable proper version upload handling instead of creating new photos

-- Add version upload flag
ALTER TABLE upload_tokens ADD COLUMN is_version_upload BOOLEAN DEFAULT 0 NOT NULL;

-- Add target photo ID for version uploads
ALTER TABLE upload_tokens ADD COLUMN target_photo_id INTEGER REFERENCES photos(id) ON DELETE CASCADE;

-- Add version label
ALTER TABLE upload_tokens ADD COLUMN version_label VARCHAR(255);

-- Add mapping type (auto/manual)
ALTER TABLE upload_tokens ADD COLUMN mapping_type VARCHAR(50);

-- Create indexes for efficient querying
CREATE INDEX idx_upload_tokens_is_version ON upload_tokens(is_version_upload);
CREATE INDEX idx_upload_tokens_target_photo ON upload_tokens(target_photo_id);
