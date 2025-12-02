-- Migration: Add permissions JSON column to users table
-- Date: 2025-12-02
-- Purpose: Store granular RBAC permissions per user

-- Add permissions column (JSONB for PostgreSQL)
ALTER TABLE users ADD COLUMN IF NOT EXISTS permissions JSONB DEFAULT '{}';

-- Add GIN index for efficient JSON queries
CREATE INDEX IF NOT EXISTS idx_users_permissions ON users USING GIN (permissions);

-- Comment explaining the permissions structure
COMMENT ON COLUMN users.permissions IS 'JSON object containing granular permissions: canCreateProjects, canEditProjects, canDeleteProjects, canViewProjects, canCreateClients, canEditClients, canDeleteClients, canViewClients, canCreateInvoices, canEditInvoices, canDeleteInvoices, canViewInvoices, canViewAnalytics, canUploadPhotos, canEditPhotos, canDeletePhotos, canManageServices, canManagePackages, canManageSettings, canManageUsers, canManageBranding, canSendNotifications, canManageCommunication';
