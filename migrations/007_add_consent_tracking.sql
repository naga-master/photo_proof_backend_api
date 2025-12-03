-- Migration: Add Consent Tracking for DPDPA 2023 Compliance
-- Description: Adds consent management tables and updates user model
-- Date: 2025-11-26

-- User Consent table (detailed consent tracking)
CREATE TABLE IF NOT EXISTS user_consents (
    id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    user_id VARCHAR(36) NOT NULL,
    
    -- Consent details
    consent_type VARCHAR(50) NOT NULL, -- 'essential', 'marketing_emails', 'sms_notifications', 'analytics'
    consent_given BOOLEAN NOT NULL DEFAULT false,
    consent_version VARCHAR(10) DEFAULT '1.0',
    
    -- Timestamps
    consent_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    withdrawal_timestamp TIMESTAMP,
    
    -- Audit trail
    ip_address VARCHAR(45),
    user_agent TEXT,
    location VARCHAR(255),
    
    -- Additional metadata
    consent_metadata JSON,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_consents_user_id ON user_consents(user_id);
CREATE INDEX IF NOT EXISTS idx_user_consents_type ON user_consents(consent_type);
CREATE INDEX IF NOT EXISTS idx_user_consents_timestamp ON user_consents(consent_timestamp);

-- Add consent fields to users table (summary fields for quick access)
ALTER TABLE users ADD COLUMN consent_given BOOLEAN DEFAULT false;
ALTER TABLE users ADD COLUMN consent_timestamp TIMESTAMP;
ALTER TABLE users ADD COLUMN consent_version VARCHAR(10) DEFAULT '1.0';
ALTER TABLE users ADD COLUMN consent_ip_address VARCHAR(45);

-- Data export requests (track when users export their data)
CREATE TABLE IF NOT EXISTS data_export_requests (
    id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    user_id VARCHAR(36) NOT NULL,
    
    -- Request details
    export_format VARCHAR(10) DEFAULT 'json', -- 'json', 'csv'
    include_contracts BOOLEAN DEFAULT true,
    include_signatures BOOLEAN DEFAULT true,
    include_activity_logs BOOLEAN DEFAULT true,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'completed', 'failed', 'expired'
    
    -- File details
    file_path TEXT,
    file_size_bytes INTEGER,
    download_url TEXT,
    expires_at TIMESTAMP, -- Download link expires in 24 hours
    
    -- Timestamps
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    downloaded_at TIMESTAMP,
    
    -- Audit
    ip_address VARCHAR(45),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_data_export_user_id ON data_export_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_data_export_status ON data_export_requests(status);

-- Account deletion requests (track deletion requests for compliance)
CREATE TABLE IF NOT EXISTS account_deletion_requests (
    id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    user_id VARCHAR(36) NOT NULL,
    
    -- Request details
    reason TEXT,
    confirmation BOOLEAN DEFAULT false,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'completed'
    rejection_reason TEXT,
    
    -- Retention check
    active_contracts_count INTEGER DEFAULT 0,
    can_delete BOOLEAN DEFAULT false,
    deletion_date TIMESTAMP, -- When deletion will/did occur
    
    -- Timestamps
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Audit
    ip_address VARCHAR(45),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_account_deletion_user_id ON account_deletion_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_account_deletion_status ON account_deletion_requests(status);

-- Add deleted_at field to users table
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP;
ALTER TABLE users ADD COLUMN deletion_reason TEXT;

-- Audit log enhancements (if not exists, otherwise skip)
-- CREATE TABLE IF NOT EXISTS audit_logs (
--     id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
--     user_id VARCHAR(36),
--     action VARCHAR(100) NOT NULL,
--     resource_type VARCHAR(50), -- 'contract', 'user', 'consent', etc.
--     resource_id VARCHAR(36),
--     details JSON,
--     ip_address VARCHAR(45),
--     user_agent TEXT,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
-- );

-- CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
-- CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
-- CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- Insert default essential consent for existing users (migration)
INSERT INTO user_consents (user_id, consent_type, consent_given, consent_version, consent_timestamp)
SELECT 
    id,
    'essential',
    true,
    '1.0',
    created_at
FROM users
WHERE NOT EXISTS (
    SELECT 1 FROM user_consents 
    WHERE user_consents.user_id = users.id 
    AND user_consents.consent_type = 'essential'
);

-- Update users table summary field
UPDATE users 
SET consent_given = true,
    consent_timestamp = created_at,
    consent_version = '1.0'
WHERE consent_given IS NULL OR consent_given = false;
