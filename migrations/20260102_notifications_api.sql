-- Migration: Add fields for public notifications API
-- Run on afkzone database

-- Add fields to admin_notifications
ALTER TABLE admin_notifications 
ADD COLUMN IF NOT EXISTS link_url VARCHAR(500) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS display_order INTEGER DEFAULT 0;

-- Add display_order to tiers (if not exists)
ALTER TABLE tiers 
ADD COLUMN IF NOT EXISTS display_order INTEGER DEFAULT 0;

-- Update existing tiers with sensible order
UPDATE tiers SET display_order = 1 WHERE tier_key = 'basic';
UPDATE tiers SET display_order = 2 WHERE tier_key = 'pro';
UPDATE tiers SET display_order = 3 WHERE tier_key = 'enterprise';
