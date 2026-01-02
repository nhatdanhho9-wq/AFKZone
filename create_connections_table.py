#!/usr/bin/env python3
"""
Create connections table for connection history tracking
"""

import sqlite3

DB_PATH = '/app/data/licenses.db'

def create_connections_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create connections table
    c.execute("""
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            peer_id TEXT,
            connection_type TEXT DEFAULT 'remote',
            ip_address TEXT,
            connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            disconnected_at TIMESTAMP,
            duration_seconds INTEGER DEFAULT 0,
            license_key TEXT,
            FOREIGN KEY (license_key) REFERENCES licenses(license_key)
        )
    """)
    conn.commit()
    print("✅ Created connections table")
    
    # Create index for faster queries
    c.execute("CREATE INDEX IF NOT EXISTS idx_connections_device_id ON connections(device_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_connections_license_key ON connections(license_key)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_connections_connected_at ON connections(connected_at)")
    conn.commit()
    print("✅ Created indexes")
    
    # Verify table structure
    c.execute("PRAGMA table_info(connections)")
    columns = [r[1] for r in c.fetchall()]
    print(f"📋 Connections table columns: {columns}")
    
    conn.close()
    print("\n✅ Done! Connections table ready for use.")

if __name__ == '__main__':
    create_connections_table()
