-- Migration: Add link_url and display_order to admin_notifications
-- Date: 2026-01-03
-- Author: OpusD Team

ALTER TABLE admin_notifications 
ADD COLUMN IF NOT EXISTS link_url VARCHAR(500);

ALTER TABLE admin_notifications 
ADD COLUMN IF NOT EXISTS display_order INTEGER DEFAULT 0;

-- Create index for better query performance
CREATE INDEX IF NOT EXISTS idx_notifications_display_order 
ON admin_notifications(display_order);
