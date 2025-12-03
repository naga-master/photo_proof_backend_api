-- Migration: Add total_comments column to projects table
-- This tracks the cached count of comments across all photos in a project

-- Add total_comments column (SQLite compatible)
ALTER TABLE projects ADD COLUMN total_comments INTEGER NOT NULL DEFAULT 0;

-- Update existing projects with their actual comment counts
UPDATE projects SET total_comments = (
    SELECT COUNT(*)
    FROM comments c
    INNER JOIN photos p ON c.photo_id = p.id
    WHERE p.project_id = projects.id
    AND c.is_deleted IS NULL
);
