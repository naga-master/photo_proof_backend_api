-- Migration 006: Add Multi-Tenant Support
-- This migration adds tables and columns for multi-tenant white-label functionality

-- Add subdomain and onboarding columns to studios table
ALTER TABLE studios ADD COLUMN IF NOT EXISTS subdomain VARCHAR(100) UNIQUE;
ALTER TABLE studios ADD COLUMN IF NOT EXISTS custom_css TEXT;
ALTER TABLE studios ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE studios ADD COLUMN IF NOT EXISTS onboarding_step VARCHAR(50);

-- Create index on subdomain
CREATE INDEX IF NOT EXISTS idx_studios_subdomain ON studios(subdomain);

-- Create studio_domains table for custom domains
CREATE TABLE IF NOT EXISTS studio_domains (
    id VARCHAR(36) PRIMARY KEY,
    studio_id VARCHAR(36) NOT NULL REFERENCES studios(id) ON DELETE CASCADE,
    domain VARCHAR(255) NOT NULL UNIQUE,
    subdomain VARCHAR(100) UNIQUE,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    verification_token VARCHAR(255),
    verification_method VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_studio_domains_domain ON studio_domains(domain);
CREATE INDEX IF NOT EXISTS idx_studio_domains_subdomain ON studio_domains(subdomain);
CREATE INDEX IF NOT EXISTS idx_studio_domains_studio_id ON studio_domains(studio_id);
CREATE INDEX IF NOT EXISTS idx_studio_domains_verified ON studio_domains(is_verified);

-- Create subscription_plans table
CREATE TABLE IF NOT EXISTS subscription_plans (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    description VARCHAR(1000),
    price_monthly DECIMAL(10, 2) NOT NULL,
    price_yearly DECIMAL(10, 2),
    max_projects INTEGER NOT NULL,
    max_storage_gb INTEGER NOT NULL,
    max_users INTEGER NOT NULL,
    max_clients INTEGER,
    features TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_visible BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_subscription_plans_active ON subscription_plans(is_active);
CREATE INDEX IF NOT EXISTS idx_subscription_plans_visible ON subscription_plans(is_visible);

-- Create studio_subscriptions table
CREATE TABLE IF NOT EXISTS studio_subscriptions (
    id VARCHAR(36) PRIMARY KEY,
    studio_id VARCHAR(36) NOT NULL REFERENCES studios(id) ON DELETE CASCADE,
    plan_id VARCHAR(36) NOT NULL REFERENCES subscription_plans(id),
    status VARCHAR(50) NOT NULL DEFAULT 'trial',
    trial_ends_at TIMESTAMP,
    current_period_start TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    current_period_end TIMESTAMP NOT NULL,
    cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
    cancelled_at TIMESTAMP,
    external_subscription_id VARCHAR(255) UNIQUE,
    external_customer_id VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_studio_subscriptions_studio_id ON studio_subscriptions(studio_id);
CREATE INDEX IF NOT EXISTS idx_studio_subscriptions_status ON studio_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_studio_subscriptions_external ON studio_subscriptions(external_subscription_id);

-- Create studio_features table
CREATE TABLE IF NOT EXISTS studio_features (
    id VARCHAR(36) PRIMARY KEY,
    studio_id VARCHAR(36) NOT NULL REFERENCES studios(id) ON DELETE CASCADE,
    feature_key VARCHAR(100) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    config TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_studio_features_studio_id ON studio_features(studio_id);
CREATE INDEX IF NOT EXISTS idx_studio_features_key ON studio_features(feature_key);
CREATE INDEX IF NOT EXISTS idx_studio_features_enabled ON studio_features(enabled);

-- Create studio_usage_stats table
CREATE TABLE IF NOT EXISTS studio_usage_stats (
    id VARCHAR(36) PRIMARY KEY,
    studio_id VARCHAR(36) NOT NULL REFERENCES studios(id) ON DELETE CASCADE,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    projects_count INTEGER NOT NULL DEFAULT 0,
    photos_uploaded INTEGER NOT NULL DEFAULT 0,
    storage_used_bytes INTEGER NOT NULL DEFAULT 0,
    api_requests INTEGER NOT NULL DEFAULT 0,
    active_users INTEGER NOT NULL DEFAULT 0,
    active_clients INTEGER NOT NULL DEFAULT 0,
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_studio_usage_stats_studio_id ON studio_usage_stats(studio_id);
CREATE INDEX IF NOT EXISTS idx_studio_usage_stats_period ON studio_usage_stats(period_start);

-- Add performance indexes for multi-tenant queries
CREATE INDEX IF NOT EXISTS idx_projects_studio_id ON projects(studio_id);
CREATE INDEX IF NOT EXISTS idx_photos_project_id ON photos(project_id);
CREATE INDEX IF NOT EXISTS idx_users_studio_id ON users(studio_id);
CREATE INDEX IF NOT EXISTS idx_clients_studio_id ON clients(studio_id);

-- Insert default subscription plans
INSERT INTO subscription_plans (id, name, display_name, description, price_monthly, price_yearly, max_projects, max_storage_gb, max_users, max_clients, features, sort_order)
VALUES 
    ('plan-starter', 'starter', 'Starter Plan', 'Perfect for individual photographers starting out', 29.00, 290.00, 10, 10, 1, 50, '{"custom_domain": false, "white_label": false, "api_access": false, "priority_support": false}', 1),
    ('plan-professional', 'professional', 'Professional Plan', 'For growing photography studios', 99.00, 990.00, 100, 100, 5, 500, '{"custom_domain": true, "white_label": true, "api_access": true, "priority_support": false}', 2),
    ('plan-enterprise', 'enterprise', 'Enterprise Plan', 'For large studios with advanced needs', 299.00, 2990.00, 999999, 1000, 20, 999999, '{"custom_domain": true, "white_label": true, "api_access": true, "priority_support": true}', 3)
ON CONFLICT (name) DO NOTHING;

-- Migration completed
SELECT 'Migration 006: Multi-tenant support tables created successfully' AS status;
