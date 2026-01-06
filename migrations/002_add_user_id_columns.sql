-- Migration 002: Add user_id columns for account-based licensing
-- Date: 2026-01-06

-- Add user_id to licenses table
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);

-- Add user_id to bank_orders table  
ALTER TABLE bank_orders ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);

-- Create indexes for user lookups
CREATE INDEX IF NOT EXISTS idx_licenses_user_id ON licenses(user_id);
CREATE INDEX IF NOT EXISTS idx_bank_orders_user_id ON bank_orders(user_id);
