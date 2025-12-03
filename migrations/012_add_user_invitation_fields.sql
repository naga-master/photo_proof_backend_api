-- Migration: Add invitation fields to users table
-- Date: 2025-12-02
-- Purpose: Support user invitation flow for studio team members

-- Add invitation fields to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS invitation_token VARCHAR(255) UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS invitation_sent_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS invitation_accepted_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS invited_by_id VARCHAR(36);

-- Create index for faster invitation token lookups
CREATE INDEX IF NOT EXISTS idx_users_invitation_token ON users(invitation_token);

-- Update existing users to have NULL values (which is the default, but being explicit)
-- This is a no-op since new columns default to NULL
