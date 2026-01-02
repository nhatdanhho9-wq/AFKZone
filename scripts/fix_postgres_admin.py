#!/usr/bin/env python3
"""
Fix admin dashboard issues - PostgreSQL version
API uses PostgreSQL, NOT SQLite!
"""

import os
import psycopg2
from psycopg2 import sql

# PostgreSQL connection string from database.py
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://afkzone:afkzone2025secure!@postgres:5432/afkzone")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def fix_products():
    conn = get_connection()
    conn.autocommit = True
    c = conn.cursor()
    
    print("=" * 50)
    print("1. CURRENT PRODUCTS STATE (PostgreSQL)")
    print("=" * 50)
    try:
        c.execute("SELECT id, name, tier, price, duration_days, max_devices, is_active, display_order FROM products ORDER BY id")
        products = c.fetchall()
        for p in products:
            print(f"  ID={p[0]}, name='{p[1]}', tier={p[2]}, price={p[3]}, days={p[4]}, max_dev={p[5]}, active={p[6]}, order={p[7]}")
    except Exception as e:
        print(f"Error reading products: {e}")
        products = []
    
    print("\n" + "=" * 50)
    print("2. RESETTING PRODUCTS TABLE")
    print("=" * 50)
    
    # Delete all products
    c.execute("DELETE FROM products")
    
    # Reset sequence/auto-increment
    c.execute("ALTER SEQUENCE products_id_seq RESTART WITH 1")
    
    # Insert clean products with proper order
    products_data = [
        ('Dùng thử 7 ngày', 'basic', 7, 0, 1, True, 1, 'Gói dùng thử miễn phí 7 ngày'),
        ('Basic 30 ngày', 'basic', 30, 50000, 1, True, 2, 'Gói Basic 30 ngày'),
        ('Basic 90 ngày', 'basic', 90, 120000, 2, True, 3, 'Gói Basic 90 ngày - tiết kiệm'),
        ('Pro 30 ngày', 'pro', 30, 100000, 5, True, 4, 'Gói Pro 30 ngày - 5 thiết bị'),
        ('Pro 90 ngày', 'pro', 90, 250000, 5, True, 5, 'Gói Pro 90 ngày - tiết kiệm'),
        ('Enterprise 30 ngày', 'enterprise', 30, 200000, 999, True, 6, 'Gói Enterprise - không giới hạn'),
        ('Enterprise 90 ngày', 'enterprise', 90, 500000, 999, True, 7, 'Gói Enterprise 90 ngày'),
        ('Test Tier 1', 'test1', 30, 80000, 2, False, 100, 'Tier thử nghiệm 1 - 2 thiết bị'),
        ('Test Tier 2', 'test2', 30, 150000, 5, False, 101, 'Tier thử nghiệm 2 - 5 thiết bị'),
    ]
    
    for p in products_data:
        c.execute("""
            INSERT INTO products (name, tier, duration_days, price, max_devices, is_active, display_order, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, p)
    
    print("  ✅ Deleted old products and created 9 clean products")
    
    # Verify
    c.execute("SELECT id, name, tier, price, is_active, display_order FROM products ORDER BY display_order")
    for p in c.fetchall():
        status = "✅ ACTIVE" if p[4] else "⏸️ INACTIVE"
        print(f"  ID={p[0]}, {p[1]}, tier={p[2]}, {p[3]:,}đ, {status}")
    
    print("\n" + "=" * 50)
    print("3. CREATING CONNECTION_LOGS TABLE")
    print("=" * 50)
    
    try:
        c.execute("""
            CREATE TABLE IF NOT EXISTS connection_logs (
                id SERIAL PRIMARY KEY,
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
        c.execute("CREATE INDEX IF NOT EXISTS idx_cl_device ON connection_logs(device_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_cl_connected ON connection_logs(connected_at)")
        print("  ✅ Created connection_logs table")
        
        # Add test data
        c.execute("DELETE FROM connection_logs")
        c.execute("""
            INSERT INTO connection_logs (device_id, remote_id, action, ip_address, license_key, peer_id, connection_type)
            VALUES ('test-device-001', 'remote-pc-001', 'connect', '192.168.1.100', 'AFK-TEST-001', 'remote-001', 'remote'),
                   ('test-device-002', 'remote-pc-002', 'connect', '192.168.1.101', 'AFK-TEST-002', 'remote-002', 'remote')
        """)
        print("  ✅ Added 2 test connection logs")
    except Exception as e:
        print(f"  ⚠️ Error with connection_logs: {e}")
    
    conn.close()
    print("\n✅ DONE! Refresh admin dashboard to see changes.")

if __name__ == '__main__':
    fix_products()
