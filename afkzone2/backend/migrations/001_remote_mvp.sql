-- Remote MVP v0.1 Database Schema
-- Migration: 001_remote_mvp.sql

-- Devices registered to accounts
CREATE TABLE IF NOT EXISTS device (
    device_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    device_name TEXT NOT NULL,
    device_type TEXT DEFAULT 'android',
    last_seen TEXT,
    online INTEGER DEFAULT 0,
    unattended_mode TEXT DEFAULT 'disabled',       -- 'disabled', 'password', 'permanent'
    permanent_password_hash TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_device_account ON device(account_id);

-- Trusted allowlist (who can remote into whom without approval)
CREATE TABLE IF NOT EXISTS trusted_allowlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_account_id TEXT NOT NULL,      -- Device owner's account
    target_device_id TEXT NOT NULL,      -- Device being accessed
    requester_account_id TEXT,           -- Who is trusted (NULL for token-based)
    requester_device_id TEXT,            -- Specific device (optional)
    status TEXT DEFAULT 'pending',       -- 'pending', 'approved', 'revoked'
    created_at TEXT,
    updated_at TEXT,
    approved_at TEXT,
    expires_at TEXT                      -- Optional expiry
);
CREATE INDEX IF NOT EXISTS idx_trusted_owner ON trusted_allowlist(owner_account_id);
CREATE INDEX IF NOT EXISTS idx_trusted_target ON trusted_allowlist(target_device_id);

-- Share tokens (short codes for guest access)
CREATE TABLE IF NOT EXISTS share_token (
    token TEXT PRIMARY KEY,              -- 6-8 char code
    device_id TEXT NOT NULL,
    account_id TEXT NOT NULL,            -- Who created it
    expires_at TEXT NOT NULL,
    max_uses INTEGER DEFAULT 1,
    uses_count INTEGER DEFAULT 0,
    revoked INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_share_device ON share_token(device_id);

-- Remote session requests (for owner approval queue)
CREATE TABLE IF NOT EXISTS remote_request (
    request_id TEXT PRIMARY KEY,
    target_device_id TEXT NOT NULL,
    requester_account_id TEXT,
    requester_device_id TEXT,
    share_token TEXT,                    -- If via token
    status TEXT DEFAULT 'pending',       -- 'pending', 'approved', 'rejected', 'expired'
    created_at TEXT,
    expires_at TEXT,
    approved_by TEXT,
    approved_at TEXT,
    session_id TEXT                      -- Created after approval
);
CREATE INDEX IF NOT EXISTS idx_request_target ON remote_request(target_device_id);
CREATE INDEX IF NOT EXISTS idx_request_status ON remote_request(status);

-- Simple accounts table for MVP (if not exists)
CREATE TABLE IF NOT EXISTS account (
    account_id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
