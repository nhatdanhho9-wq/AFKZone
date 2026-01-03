-- Migration: Add device_alias column to license_devices
-- Date: 2026-01-04
-- Version: 2.2.56
-- 
-- Table: license_devices
-- Column: device_alias
-- Type: VARCHAR(100)
-- Nullable: YES (default NULL)
-- Index: Yes (idx_license_devices_alias)
-- Purpose: User-friendly device naming for multi-device licenses

-- Add device_alias column (nullable, default NULL)
ALTER TABLE license_devices 
ADD COLUMN IF NOT EXISTS device_alias VARCHAR(100) DEFAULT NULL;

-- Add index for faster alias lookups and searches
CREATE INDEX IF NOT EXISTS idx_license_devices_alias 
ON license_devices(device_alias) 
WHERE device_alias IS NOT NULL;

-- Verify migration
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'license_devices' 
AND column_name = 'device_alias';

-- Sample query to confirm UI can safely use device_alias
-- SELECT device_id, COALESCE(device_alias, 'Unnamed Device') as alias FROM license_devices;
