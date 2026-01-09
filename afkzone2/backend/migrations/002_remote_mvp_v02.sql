-- Remote MVP v0.2 Schema Upgrades
-- Migration: 002_remote_mvp_v02.sql

-- Track active device sessions for fan-out notifications
ALTER TABLE device ADD COLUMN current_session_id TEXT;
ALTER TABLE device ADD COLUMN session_started_at TEXT;

-- Add controller device to trusted pair (for auto-approve by device, not just account)
ALTER TABLE trusted_allowlist ADD COLUMN controller_device_id TEXT;

-- Device session history (for account switch tracking)
CREATE TABLE IF NOT EXISTS device_session_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    action TEXT NOT NULL,  -- 'login', 'logout', 'switch_out'
    ts TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_device_session_device ON device_session_history(device_id);

-- Session blacklist for invalidated tokens
CREATE TABLE IF NOT EXISTS session_blacklist (
    token_hash TEXT PRIMARY KEY,
    invalidated_at TEXT NOT NULL,
    reason TEXT
);
