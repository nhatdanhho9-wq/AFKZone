-- Migration 003: Add alias and last_seen to license_devices
-- Date: 2026-01-06

-- Add alias column (user-friendly device name)
ALTER TABLE license_devices ADD COLUMN IF NOT EXISTS alias VARCHAR(255);

-- Add last_seen column (for device activity tracking)
ALTER TABLE license_devices ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW();
