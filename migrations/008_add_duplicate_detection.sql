-- Migration: Add Duplicate Detection Support
-- Description: Add content hash for photos, indexes for duplicate detection
-- Date: 2025-11-27

-- Photo content hash for duplicate detection within projects
ALTER TABLE photos ADD COLUMN content_hash VARCHAR(64);

-- Indexes for fast duplicate lookups
CREATE INDEX idx_photos_content_hash ON photos(content_hash) WHERE content_hash IS NOT NULL;
CREATE INDEX idx_photos_project_hash ON photos(project_id, content_hash);

-- Photo filename index for quick lookups
CREATE INDEX idx_photos_project_filename ON photos(project_id, original_filename);

-- Folder name uniqueness per project (case-insensitive)
-- Note: This creates a unique constraint so duplicate folder names will be rejected at database level
CREATE UNIQUE INDEX idx_folders_project_name_unique ON folders(project_id, LOWER(name));

-- Client phone index for duplicate warnings
CREATE INDEX idx_clients_phone ON clients(phone) WHERE phone IS NOT NULL;

-- Rollback instructions (if needed):
-- DROP INDEX IF EXISTS idx_clients_phone;
-- DROP INDEX IF EXISTS idx_folders_project_name_unique;
-- DROP INDEX IF EXISTS idx_photos_project_filename;
-- DROP INDEX IF EXISTS idx_photos_project_hash;
-- DROP INDEX IF EXISTS idx_photos_content_hash;
-- ALTER TABLE photos DROP COLUMN content_hash;
