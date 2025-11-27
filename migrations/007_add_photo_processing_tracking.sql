-- Migration: Add photo processing tracking fields
-- This migration adds fields to track background processing of photo variants

ALTER TABLE photos ADD COLUMN processing_error TEXT;
ALTER TABLE photos ADD COLUMN processing_attempts INTEGER DEFAULT 0;
ALTER TABLE photos ADD COLUMN last_processing_attempt_at TIMESTAMP;
