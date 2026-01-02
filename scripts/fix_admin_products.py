#!/usr/bin/env python3
"""
Fix admin dashboard issues:
1. Clean up products table - reset IDs, add test tiers
2. Add proper sorting
3. Check connections table structure
"""

import sqlite3

DB_PATH = '/app/data/licenses.db'

def fix_admin_issues():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("=" * 50)
    print("1. CURRENT PRODUCTS STATE")
    print("=" * 50)
    c.execute("SELECT id, name, tier, price, duration_days, max_devices, is_active, display_order FROM products ORDER BY id")
    products = c.fetchall()
    for p in products:
        print(f"  ID={p[0]}, name='{p[1]}', tier={p[2]}, price={p[3]}, days={p[4]}, max_dev={p[5]}, active={p[6]}, order={p[7]}")
    
    print("\n" + "=" * 50)
    print("2. FIXING PRODUCTS - DELETE ALL AND RECREATE WITH CLEAN IDs")
    print("=" * 50)
    
    # Delete all products
    c.execute("DELETE FROM products")
    
    # Reset auto-increment
    c.execute("DELETE FROM sqlite_sequence WHERE name='products'")
    
    # Insert clean products with proper order
    products_data = [
        # ID=1: Trial
        ('Dùng thử 7 ngày', 'basic', 7, 0, 1, 1, 1, 'Gói dùng thử miễn phí 7 ngày'),
        # ID=2: Basic 30
        ('Basic 30 ngày', 'basic', 30, 50000, 1, 1, 2, 'Gói Basic 30 ngày'),
        # ID=3: Basic 90
        ('Basic 90 ngày', 'basic', 90, 120000, 2, 1, 3, 'Gói Basic 90 ngày - tiết kiệm'),
        # ID=4: Pro 30
        ('Pro 30 ngày', 'pro', 30, 100000, 5, 1, 4, 'Gói Pro 30 ngày - 5 thiết bị'),
        # ID=5: Pro 90
        ('Pro 90 ngày', 'pro', 90, 250000, 5, 1, 5, 'Gói Pro 90 ngày - tiết kiệm'),
        # ID=6: Enterprise 30
        ('Enterprise 30 ngày', 'enterprise', 30, 200000, 999, 1, 6, 'Gói Enterprise - không giới hạn'),
        # ID=7: Enterprise 90
        ('Enterprise 90 ngày', 'enterprise', 90, 500000, 999, 1, 7, 'Gói Enterprise 90 ngày'),
        # ID=8: Test1 (INACTIVE)
        ('Test Tier 1', 'test1', 30, 80000, 2, 0, 100, 'Tier thử nghiệm 1 - 2 thiết bị'),
        # ID=9: Test2 (INACTIVE)
        ('Test Tier 2', 'test2', 30, 150000, 5, 0, 101, 'Tier thử nghiệm 2 - 5 thiết bị'),
    ]
    
    c.executemany("""
        INSERT INTO products (name, tier, duration_days, price, max_devices, is_active, display_order, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, products_data)
    conn.commit()
    print("  ✅ Deleted old products and created 9 clean products")
    
    # Verify
    c.execute("SELECT id, name, tier, price, is_active, display_order FROM products ORDER BY display_order")
    for p in c.fetchall():
        status = "✅ ACTIVE" if p[4] else "⏸️ INACTIVE"
        print(f"  ID={p[0]}, {p[1]}, tier={p[2]}, {p[3]:,}đ, {status}")
    
    print("\n" + "=" * 50)
    print("3. SYNC PRICING TABLE")
    print("=" * 50)
    c.execute("DELETE FROM pricing")
    c.execute("""
        INSERT INTO pricing (tier, duration_days, price, max_devices)
        SELECT tier, duration_days, price, max_devices FROM products WHERE is_active=1
    """)
    conn.commit()
    print("  ✅ Synced pricing table from active products")
    
    print("\n" + "=" * 50)
    print("4. CHECK CONNECTIONS TABLE")
    print("=" * 50)
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='connections'")
    if c.fetchone():
        c.execute("PRAGMA table_info(connections)")
        cols = [r[1] for r in c.fetchall()]
        print(f"  ✅ Connections table exists with columns: {cols}")
        c.execute("SELECT COUNT(*) FROM connections")
        print(f"  📊 Current connections count: {c.fetchone()[0]}")
    else:
        print("  ❌ Connections table does not exist!")
    
    conn.close()
    print("\n✅ DONE!")

if __name__ == '__main__':
    fix_admin_issues()
