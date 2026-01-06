#!/usr/bin/env python3
"""
Account-Based Licensing - Database Migration
Creates users table and adds user_id columns to licenses/bank_orders
"""
from database import get_db
from sqlalchemy import text

db = next(get_db())

print("=== ACCOUNT-BASED LICENSING MIGRATION ===\n")

# 1. Create users table if not exists
print("1. Creating users table...")
try:
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255),
            name VARCHAR(255),
            google_id VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW(),
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
    """))
    db.commit()
    print("   ✅ users table created")
except Exception as e:
    print(f"   ❌ Error: {e}")
    db.rollback()

# 2. Add user_id to licenses
print("2. Adding user_id to licenses table...")
try:
    # Check if column exists
    exists = db.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='licenses' AND column_name='user_id'
    """)).fetchone()
    
    if not exists:
        db.execute(text("""
            ALTER TABLE licenses ADD COLUMN user_id INTEGER REFERENCES users(id)
        """))
        db.commit()
        print("   ✅ user_id column added to licenses")
    else:
        print("   ⏭️ user_id column already exists")
except Exception as e:
    print(f"   ❌ Error: {e}")
    db.rollback()

# 3. Add user_id to bank_orders
print("3. Adding user_id to bank_orders table...")
try:
    exists = db.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='bank_orders' AND column_name='user_id'
    """)).fetchone()
    
    if not exists:
        db.execute(text("""
            ALTER TABLE bank_orders ADD COLUMN user_id INTEGER REFERENCES users(id)
        """))
        db.commit()
        print("   ✅ user_id column added to bank_orders")
    else:
        print("   ⏭️ user_id column already exists")
except Exception as e:
    print(f"   ❌ Error: {e}")
    db.rollback()

# 4. Add alias column to license_devices if not exists
print("4. Adding alias to license_devices...")
try:
    exists = db.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='license_devices' AND column_name='alias'
    """)).fetchone()
    
    if not exists:
        db.execute(text("""
            ALTER TABLE license_devices ADD COLUMN alias VARCHAR(255)
        """))
        db.commit()
        print("   ✅ alias column added to license_devices")
    else:
        print("   ⏭️ alias column already exists")
except Exception as e:
    print(f"   ❌ Error: {e}")
    db.rollback()

# 5. Add last_seen to license_devices if not exists
print("5. Adding last_seen to license_devices...")
try:
    exists = db.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='license_devices' AND column_name='last_seen'
    """)).fetchone()
    
    if not exists:
        db.execute(text("""
            ALTER TABLE license_devices ADD COLUMN last_seen TIMESTAMP DEFAULT NOW()
        """))
        db.commit()
        print("   ✅ last_seen column added to license_devices")
    else:
        print("   ⏭️ last_seen column already exists")
except Exception as e:
    print(f"   ❌ Error: {e}")
    db.rollback()

print("\n=== MIGRATION COMPLETE ===")

# Verify
print("\nVerifying schema...")
users_cols = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users'")).fetchall()
print(f"users columns: {[c[0] for c in users_cols]}")

lic_user = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='licenses' AND column_name='user_id'")).fetchone()
print(f"licenses.user_id: {'✅ exists' if lic_user else '❌ missing'}")

bo_user = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='bank_orders' AND column_name='user_id'")).fetchone()
print(f"bank_orders.user_id: {'✅ exists' if bo_user else '❌ missing'}")
