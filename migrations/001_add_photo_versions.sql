-- Migration: Add Photo Versions Support
-- Date: 2024-11-14
-- Description: Add photo versioning system for edited photos

-- Create photo_versions table
CREATE TABLE IF NOT EXISTS photo_versions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  photo_id INTEGER NOT NULL,
  version_number INTEGER NOT NULL,
  
  -- File storage
  src VARCHAR(1000) NOT NULL,
  storage_path VARCHAR(1000) NOT NULL,
  thumbnail_path VARCHAR(1000),
  preview_path VARCHAR(1000),
  
  -- File metadata
  original_filename VARCHAR(500) NOT NULL,
  file_size INTEGER NOT NULL,
  mime_type VARCHAR(100) NOT NULL,
  width INTEGER NOT NULL,
  height INTEGER NOT NULL,
  
  -- Version metadata
  is_original BOOLEAN DEFAULT 0,
  version_label VARCHAR(200),
  replaced_version_id INTEGER,
  
  -- Upload tracking
  uploaded_by VARCHAR(36) NOT NULL,
  upload_note TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  
  -- Foreign keys
  FOREIGN KEY(photo_id) REFERENCES photos(id) ON DELETE CASCADE,
  FOREIGN KEY(replaced_version_id) REFERENCES photo_versions(id) ON DELETE SET NULL,
  FOREIGN KEY(uploaded_by) REFERENCES users(id),
  
  -- Constraints
  UNIQUE(photo_id, version_number),
  CHECK(version_number > 0),
  CHECK(version_number <= 100)
);

-- Add version columns to photos table
ALTER TABLE photos ADD COLUMN current_version_id INTEGER REFERENCES photo_versions(id);
ALTER TABLE photos ADD COLUMN version_count INTEGER NOT NULL DEFAULT 1;
ALTER TABLE photos ADD COLUMN last_version_updated_at DATETIME;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_photo_versions_photo_id ON photo_versions(photo_id);
CREATE INDEX IF NOT EXISTS ix_photo_versions_created_at ON photo_versions(created_at);
CREATE INDEX IF NOT EXISTS ix_photos_current_version ON photos(current_version_id);

-- Note: After running this migration, you should run the data migration script
-- to create initial version records for existing photos
