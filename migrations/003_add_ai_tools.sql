-- Migration: Add AI Tools table
-- Date: 2025-11-16
-- Description: Create ai_tools table to store AI tool information with thumbnail paths

CREATE TABLE IF NOT EXISTS ai_tools (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    thumbnail_path TEXT NOT NULL,
    tool_id TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1,
    order_index INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_tools_tool_id ON ai_tools(tool_id);
CREATE INDEX IF NOT EXISTS idx_ai_tools_is_active ON ai_tools(is_active);
CREATE INDEX IF NOT EXISTS idx_ai_tools_order_index ON ai_tools(order_index);

-- Insert initial AI tools
INSERT INTO ai_tools (id, name, description, thumbnail_path, tool_id, is_active, order_index)
VALUES 
    (
        lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6))),
        'AI Photo Booth',
        'Create fun, AI-generated photos with various styles.',
        'data/images/AI_image_generator.webp',
        'photoBooth',
        1,
        1
    ),
    (
        lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6))),
        'Historic Imager',
        'Transform portraits into historical figures with AI.',
        'data/images/transform_portrait.png',
        'historicImager',
        1,
        2
    ),
    (
        lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6))),
        'Virtual Try-On',
        'See how clothing items look on models or clients.',
        'data/images/virtual_try_on.webp',
        'virtualTryOn',
        1,
        3
    );
