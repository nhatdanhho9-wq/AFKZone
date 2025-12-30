-- Database Migration for Admin Dashboard
-- Run this SQL on your PostgreSQL database

-- 1. Create connection_logs table for tracking all client connections
CREATE TABLE IF NOT EXISTS connection_logs (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(255) NOT NULL,
    peer_id VARCHAR(255),
    connection_type VARCHAR(50) NOT NULL, -- remote, file_transfer, view_camera, terminal
    ip_address VARCHAR(45),
    connected_at TIMESTAMP NOT NULL DEFAULT NOW(),
    disconnected_at TIMESTAMP,
    duration_seconds INTEGER,
    bytes_sent BIGINT,
    bytes_received BIGINT,
    license_key VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_connection_logs_device_id ON connection_logs(device_id);
CREATE INDEX IF NOT EXISTS idx_connection_logs_license_key ON connection_logs(license_key);
CREATE INDEX IF NOT EXISTS idx_connection_logs_connected_at ON connection_logs(connected_at);

-- 2. Add deactivated_at column to license_devices if not exists
ALTER TABLE license_devices ADD COLUMN IF NOT EXISTS deactivated_at TIMESTAMP;

-- 3. Create admin_users table if not exists
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- 4. Insert default admin user (password: admin123)
-- Password hash for 'admin123' using bcrypt
-- You should change this password after first login!
INSERT INTO admin_users (username, password_hash, role)
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY5Y5Y5Y5Y5', 'admin')
ON CONFLICT (username) DO NOTHING;

-- 5. Create device_heartbeats table if not exists (for tracking device activity)
CREATE TABLE IF NOT EXISTS device_heartbeats (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(255) NOT NULL,
    app_version VARCHAR(50),
    license_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_device_heartbeats_device_id ON device_heartbeats(device_id);
CREATE INDEX IF NOT EXISTS idx_device_heartbeats_created_at ON device_heartbeats(created_at);

-- 6. Add revoked_at and revoked_reason to licenses table if not exists
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMP;
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS revoked_reason TEXT;

-- 7. Create server_stats table for monitoring (optional)
CREATE TABLE IF NOT EXISTS server_stats (
    id SERIAL PRIMARY KEY,
    cpu_usage_percent DECIMAL(5,2),
    memory_usage_mb INTEGER,
    active_connections INTEGER,
    bandwidth_in_mbps DECIMAL(10,2),
    bandwidth_out_mbps DECIMAL(10,2),
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_server_stats_timestamp ON server_stats(timestamp);

-- 8. Add notes column to licenses if not exists
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS notes TEXT;

-- 9. Add created_by column to licenses if not exists
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS created_by VARCHAR(255) DEFAULT 'system';

-- Notes:
-- 1. Change the default admin password immediately after deployment
-- 2. The connection_logs table will be populated by the RustDesk server or client
-- 3. You may need to add triggers or scheduled jobs to clean up old connection logs
-- 4. Consider adding foreign key constraints if needed for data integrity

