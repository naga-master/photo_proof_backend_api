-- Migration: Change email/username from global unique to per-studio unique
-- Date: 2025-12-02
-- Purpose: Allow same person to be in multiple studios

-- Step 1: Drop existing global unique indexes/constraints on users table
DROP INDEX IF EXISTS ix_users_email;
DROP INDEX IF EXISTS ix_users_username;

-- Step 2: Create composite unique indexes (email + studio_id, username + studio_id)
-- Using partial index to handle NULL studio_id (for system users without studio)
CREATE UNIQUE INDEX ix_users_email_studio ON users(email, studio_id) WHERE studio_id IS NOT NULL;
CREATE UNIQUE INDEX ix_users_username_studio ON users(username, studio_id) WHERE studio_id IS NOT NULL;

-- For users without studio_id (NULL), maintain global uniqueness
CREATE UNIQUE INDEX ix_users_email_no_studio ON users(email) WHERE studio_id IS NULL;
CREATE UNIQUE INDEX ix_users_username_no_studio ON users(username) WHERE studio_id IS NULL;

-- Step 3: Create regular (non-unique) indexes for email/username lookups
CREATE INDEX IF NOT EXISTS ix_users_email_lookup ON users(email);
CREATE INDEX IF NOT EXISTS ix_users_username_lookup ON users(username);
