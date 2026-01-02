#!/usr/bin/env python3
"""
Create products table and add test tiers
"""

import sqlite3

DB_PATH = '/app/data/licenses.db'

def create_products_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create products table if not exists
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            tier TEXT NOT NULL,
            duration_days INTEGER NOT NULL,
            price INTEGER NOT NULL DEFAULT 0,
            max_devices INTEGER NOT NULL DEFAULT 1,
            is_active BOOLEAN DEFAULT TRUE,
            display_order INTEGER DEFAULT 0,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    print("✅ Created products table")
    
    # Check existing products
    c.execute("SELECT COUNT(*) FROM products")
    count = c.fetchone()[0]
    print(f"📦 Current products: {count}")
    
    if count == 0:
        # Add default products
        products_data = [
            # Basic tier
            ('Basic 7 Days Trial', 'basic', 7, 0, 1, 1, 1, 'Free 7-day trial'),
            ('Basic 30 Days', 'basic', 30, 50000, 1, 1, 2, 'Basic 30 days - 1 device'),
            # Pro tier
            ('Pro 30 Days', 'pro', 30, 100000, 3, 1, 3, 'Pro 30 days - 3 devices'),
            # Enterprise tier
            ('Enterprise 30 Days', 'enterprise', 30, 200000, 10, 1, 4, 'Enterprise 30 days - 10 devices'),
            # Test tiers (inactive by default)
            ('Test Tier 1', 'test1', 30, 100000, 2, 0, 10, 'Test tier 1 - 2 devices'),
            ('Test Tier 2', 'test2', 30, 200000, 5, 0, 11, 'Test tier 2 - 5 devices'),
        ]
        
        c.executemany("""
            INSERT INTO products (name, tier, duration_days, price, max_devices, is_active, display_order, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, products_data)
        conn.commit()
        print("✅ Added default products including 2 test tiers (inactive)")
    
    # Create pricing table for backwards compatibility if needed
    c.execute("""
        CREATE TABLE IF NOT EXISTS pricing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tier TEXT NOT NULL,
            duration_days INTEGER NOT NULL,
            price INTEGER NOT NULL DEFAULT 0,
            max_devices INTEGER NOT NULL DEFAULT 1,
            UNIQUE(tier, duration_days)
        )
    """)
    conn.commit()
    print("✅ Created pricing table")
    
    # Sync pricing from products
    c.execute("DELETE FROM pricing")
    c.execute("""
        INSERT INTO pricing (tier, duration_days, price, max_devices)
        SELECT tier, duration_days, price, max_devices FROM products WHERE is_active=1
    """)
    conn.commit()
    print("✅ Synced pricing table from products")
    
    # Show final products
    print("\n📦 Final products:")
    c.execute("SELECT id, name, tier, price, duration_days, max_devices, is_active FROM products ORDER BY display_order")
    for p in c.fetchall():
        status = "✅ ACTIVE" if p[6] else "⏸️ INACTIVE"
        print(f"  ID={p[0]}, {p[1]}, tier={p[2]}, price={p[3]}đ, {p[4]} days, {p[5]} devices, {status}")
    
    conn.close()
    print("\n✅ Done! Use admin dashboard to toggle tiers.")

if __name__ == '__main__':
    create_products_table()
