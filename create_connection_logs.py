#!/usr/bin/env python3
"""
Create connection_logs table as expected by the API endpoints
"""

import sqlite3

DB_PATH = '/app/data/licenses.db'

def create_connection_logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check existing tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%connection%'")
    tables = [r[0] for r in c.fetchall()]
    print(f"Existing connection-related tables: {tables}")
    
    # Drop old 'connections' table if exists and create 'connection_logs' as API expects
    c.execute("DROP TABLE IF EXISTS connections")
    
    # Create connection_logs table matching the API schema (from app.py lines 1932-1943)
    c.execute("""
        CREATE TABLE IF NOT EXISTS connection_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            remote_id TEXT,
            action TEXT DEFAULT 'connect',
            ip_address TEXT,
            connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            disconnected_at TIMESTAMP,
            duration_seconds INTEGER DEFAULT 0,
            license_key TEXT,
            peer_id TEXT,
            connection_type TEXT DEFAULT 'remote'
        )
    """)
    conn.commit()
    print("✅ Created connection_logs table")
    
    # Create indexes
    c.execute("CREATE INDEX IF NOT EXISTS idx_connection_logs_device_id ON connection_logs(device_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_connection_logs_connected_at ON connection_logs(connected_at)")
    conn.commit()
    print("✅ Created indexes")
    
    # Insert some test data so user can see it working
    test_data = [
        ('test-device-001', 'remote-pc-001', 'connect', '192.168.1.100', 'AFK-TEST-001', 'remote-001', 'remote'),
        ('test-device-002', 'remote-pc-002', 'connect', '192.168.1.101', 'AFK-TEST-002', 'remote-002', 'remote'),
    ]
    c.executemany("""
        INSERT INTO connection_logs (device_id, remote_id, action, ip_address, license_key, peer_id, connection_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, test_data)
    conn.commit()
    print("✅ Added 2 test connection logs")
    
    # Verify
    c.execute("SELECT * FROM connection_logs")
    for r in c.fetchall():
        print(f"  {r}")
    
    conn.close()
    print("\n✅ DONE! Connection logs table ready.")

if __name__ == '__main__':
    create_connection_logs()
