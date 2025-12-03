-- Migration: Add unique constraint for photo filenames within folders
-- Photos must have unique filenames within their folder

-- Add unique constraint: photo filename must be unique within folder
-- (project_id + folder_id + original_filename must be unique)
-- Note: folder_id can be NULL for photos not in folders
CREATE UNIQUE INDEX IF NOT EXISTS idx_photos_filename_per_folder 
ON photos (project_id, folder_id, original_filename);

-- For photos without folders (folder_id IS NULL), also enforce uniqueness
CREATE UNIQUE INDEX IF NOT EXISTS idx_photos_filename_no_folder
ON photos (project_id, original_filename)
WHERE folder_id IS NULL;

-- Add comment explaining the constraint
COMMENT ON INDEX idx_photos_filename_per_folder IS 
'Ensures photo filenames are unique within each folder. Different folders can have photos with the same filename.';

COMMENT ON INDEX idx_photos_filename_no_folder IS 
'Ensures photo filenames are unique within project for photos not in folders.';
