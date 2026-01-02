#!/usr/bin/env python3
"""
Script để thêm 2 tiers mới (test1, test2) và thêm trường 'is_active' cho toggle tiers.
Chạy trên Docker container: docker exec afkzone-license-api python3 /app/add_tiers_with_toggle.py
"""

import sqlite3

DB_PATH = '/app/data/licenses.db'

def add_tiers_with_toggle():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Check if products table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
    if not c.fetchone():
        print("❌ Error: 'products' table does not exist!")
        conn.close()
        return
    
    # 2. Add 'is_active' column if not exists
    c.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in c.fetchall()]
    print(f"📋 Current columns: {columns}")
    
    if 'is_active' not in columns:
        print("➕ Adding 'is_active' column...")
        c.execute("ALTER TABLE products ADD COLUMN is_active INTEGER DEFAULT 1")
        # Set all existing products to active
        c.execute("UPDATE products SET is_active = 1 WHERE is_active IS NULL")
        conn.commit()
        print("✅ Added 'is_active' column")
    else:
        print("✅ 'is_active' column already exists")
    
    # 3. Check existing products
    c.execute("SELECT id, name, tier, price, duration_days, max_devices, is_active FROM products ORDER BY id")
    existing = c.fetchall()
    print(f"\n📦 Existing products ({len(existing)}):")
    for p in existing:
        print(f"  ID={p[0]}, name='{p[1]}', tier={p[2]}, price={p[3]}, days={p[4]}, max_dev={p[5]}, active={p[6]}")
    
    # 4. Add test tiers if not exist
    # Check if test1 tier exists
    c.execute("SELECT id FROM products WHERE tier = 'test1' LIMIT 1")
    if not c.fetchone():
        print("\n➕ Adding test1 tier products...")
        # test1: 30 days, 2 devices, 100k VND
        c.execute("""
            INSERT INTO products (name, tier, price, duration_days, max_devices, is_active, description)
            VALUES ('Test Tier 1', 'test1', 100000, 30, 2, 0, 'Test tier 1 - 2 devices')
        """)
        print("  ✅ Added test1 tier (30 days, 2 devices, 100k VND, INACTIVE)")
    else:
        print("\n✅ test1 tier already exists")
    
    # Check if test2 tier exists
    c.execute("SELECT id FROM products WHERE tier = 'test2' LIMIT 1")
    if not c.fetchone():
        print("➕ Adding test2 tier products...")
        # test2: 30 days, 5 devices, 200k VND
        c.execute("""
            INSERT INTO products (name, tier, price, duration_days, max_devices, is_active, description)
            VALUES ('Test Tier 2', 'test2', 200000, 30, 5, 0, 'Test tier 2 - 5 devices')
        """)
        print("  ✅ Added test2 tier (30 days, 5 devices, 200k VND, INACTIVE)")
    else:
        print("\n✅ test2 tier already exists")
    
    conn.commit()
    
    # 5. Show final products
    print("\n📦 Final products:")
    c.execute("SELECT id, name, tier, price, duration_days, max_devices, is_active FROM products ORDER BY id")
    for p in c.fetchall():
        status = "✅ ACTIVE" if p[6] == 1 else "⏸️ INACTIVE"
        print(f"  ID={p[0]}, name='{p[1]}', tier={p[2]}, price={p[3]}đ, {p[4]} days, {p[5]} devices, {status}")
    
    conn.close()
    print("\n✅ Done! To toggle a tier, use admin dashboard or update is_active column manually.")

if __name__ == '__main__':
    add_tiers_with_toggle()
