#!/bin/bash
# Setup Admin Dashboard on server

cd ~/license-api

# 1. Create tables
docker exec afkzone-license-api python3 << 'PYEOF'
from database import get_db
from sqlalchemy import text

db = next(get_db())

# Create connection_logs table
db.execute(text("""
CREATE TABLE IF NOT EXISTS connection_logs (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(255) NOT NULL,
    peer_id VARCHAR(255),
    connection_type VARCHAR(50) NOT NULL,
    ip_address VARCHAR(45),
    connected_at TIMESTAMP NOT NULL DEFAULT NOW(),
    disconnected_at TIMESTAMP,
    duration_seconds INTEGER,
    bytes_sent BIGINT,
    bytes_received BIGINT,
    license_key VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
)
"""))

# Create admin_users table
db.execute(text("""
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
)
"""))

# Add columns to existing tables
db.execute(text("ALTER TABLE license_devices ADD COLUMN IF NOT EXISTS deactivated_at TIMESTAMP"))
db.execute(text("ALTER TABLE licenses ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMP"))
db.execute(text("ALTER TABLE licenses ADD COLUMN IF NOT EXISTS revoked_reason TEXT"))
db.execute(text("ALTER TABLE licenses ADD COLUMN IF NOT EXISTS notes TEXT"))
db.execute(text("ALTER TABLE licenses ADD COLUMN IF NOT EXISTS created_by VARCHAR(255) DEFAULT 'system'"))

db.commit()
print("✅ Tables created/updated")
PYEOF

# 2. Create admin user
docker exec afkzone-license-api python3 << 'PYEOF'
from database import get_db
from sqlalchemy import text
import bcrypt

db = next(get_db())
pw_hash = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode()

db.execute(text("""
    INSERT INTO admin_users (username, password_hash, role)
    VALUES ('admin', :hash, 'admin')
    ON CONFLICT (username) DO NOTHING
"""), {"hash": pw_hash})

db.commit()
print("✅ Admin user created (username: admin, password: admin123)")
PYEOF

# 3. Add endpoints to app.py (simple append)
echo "" >> app.py
echo "# ==================== ADMIN ENDPOINTS - ADDED BY SETUP ====================" >> app.py
cat admin_endpoints_simple.py >> app.py

# 4. Restart API
docker restart afkzone-license-api
sleep 3
echo "✅ API restarted"

echo ""
echo "🎉 Admin Dashboard setup complete!"
echo "📝 Login: https://api.afkzone.cloud/admin"
echo "👤 Username: admin"
echo "🔑 Password: admin123"
echo ""
echo "⚠️  IMPORTANT: Change password after first login!"

