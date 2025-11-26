-- Migration: Add Contract Management Tables
-- Description: Creates tables for digital contracts with e-signatures
-- Date: 2025-11-26
-- SQLite compatible version

-- Contract Templates table
CREATE TABLE IF NOT EXISTS contract_templates (
    id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    studio_id VARCHAR(36) NOT NULL REFERENCES studios(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50),
    content TEXT NOT NULL,
    variables JSON,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contracts table
CREATE TABLE IF NOT EXISTS contracts (
    id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    studio_id VARCHAR(36) NOT NULL REFERENCES studios(id) ON DELETE CASCADE,
    client_id VARCHAR(36) NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    project_id VARCHAR(36) REFERENCES projects(id) ON DELETE SET NULL,
    template_id VARCHAR(36) REFERENCES contract_templates(id) ON DELETE SET NULL,
    
    -- Contract details
    contract_number VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    terms JSON,
    
    -- Status
    status VARCHAR(50) DEFAULT 'draft',
    
    -- Dates
    sent_at TIMESTAMP,
    viewed_at TIMESTAMP,
    signed_at TIMESTAMP,
    expires_at TIMESTAMP,
    
    -- Signature data
    client_signature TEXT,
    client_signature_hash VARCHAR(256),
    client_ip VARCHAR(45),
    client_user_agent TEXT,
    
    -- PDF storage
    pdf_url TEXT,
    signed_pdf_url TEXT,
    
    -- Metadata
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contract Activity Log table
CREATE TABLE IF NOT EXISTS contract_activities (
    id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    contract_id VARCHAR(36) NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL, -- created, sent, viewed, signed, downloaded
    actor_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Email Templates for Contracts
CREATE TABLE IF NOT EXISTS contract_email_templates (
    id VARCHAR(36) PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    studio_id VARCHAR(36) NOT NULL REFERENCES studios(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- 'signature_request', 'reminder', 'signed_confirmation'
    subject VARCHAR(255) NOT NULL,
    body_html TEXT NOT NULL,
    body_text TEXT NOT NULL,
    variables JSON,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_contract_templates_studio ON contract_templates(studio_id);

CREATE INDEX IF NOT EXISTS idx_contracts_studio ON contracts(studio_id);
CREATE INDEX IF NOT EXISTS idx_contracts_client ON contracts(client_id);
CREATE INDEX IF NOT EXISTS idx_contracts_project ON contracts(project_id);
CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status);
CREATE INDEX IF NOT EXISTS idx_contracts_contract_number ON contracts(contract_number);

CREATE INDEX IF NOT EXISTS idx_contract_activities_contract ON contract_activities(contract_id);
CREATE INDEX IF NOT EXISTS idx_contract_activities_actor ON contract_activities(actor_id);

CREATE INDEX IF NOT EXISTS idx_contract_email_templates_studio ON contract_email_templates(studio_id);

-- Create sample contract templates for testing
INSERT INTO contract_templates (id, studio_id, name, category, content, is_active)
SELECT 
    lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6))),
    s.id,
    'Standard Photography Contract',
    'wedding',
    '# Photography Services Agreement

This Agreement is entered into on {{date}} between {{studio_name}} ("Photographer") and {{client_name}} ("Client").

## 1. Services
The Photographer agrees to provide photography services for the following event:
- Event Type: {{event_type}}
- Date: {{event_date}}
- Location: {{location}}
- Duration: {{duration}}

## 2. Deliverables
The Photographer will provide:
- {{num_photos}} edited high-resolution digital images
- Online gallery access for {{gallery_duration}} days
- Print release for personal use

## 3. Payment Terms
- Total Package Price: ${{total_price}}
- Deposit (50%): ${{deposit_amount}} (due upon signing)
- Balance: ${{balance_amount}} (due 7 days before event)

## 4. Cancellation Policy
- Cancellation by Client: Deposit is non-refundable
- Cancellation by Photographer: Full refund of all payments

## 5. Copyright and Usage
The Photographer retains copyright of all images. Client receives personal use license.

## 6. Liability
The Photographer''s liability is limited to the return of all payments received.

By signing below, both parties agree to the terms of this agreement.',
    true
FROM studios s
LIMIT 1;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_contracts_expires_at ON contracts(expires_at) WHERE status IN ('sent', 'viewed');
CREATE INDEX IF NOT EXISTS idx_contracts_signed_at ON contracts(signed_at) WHERE status = 'signed';
