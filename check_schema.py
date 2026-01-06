#!/usr/bin/env python3
"""Check current database schema"""
from database import get_db
from sqlalchemy import text

db = next(get_db())

# Get all tables
print("=== TABLES ===")
tables = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")).fetchall()
for t in tables:
    print(f"  - {t[0]}")

# Check licenses table structure
print("\n=== LICENSES TABLE ===")
try:
    cols = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='licenses'")).fetchall()
    for c in cols:
        print(f"  {c[0]}: {c[1]}")
except Exception as e:
    print(f"  Error: {e}")

# Check if users table exists
print("\n=== USERS TABLE ===")
try:
    cols = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='users'")).fetchall()
    if cols:
        for c in cols:
            print(f"  {c[0]}: {c[1]}")
    else:
        print("  Table does not exist")
except Exception as e:
    print(f"  Error: {e}")

# Check bank_orders
print("\n=== BANK_ORDERS TABLE ===")
try:
    cols = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='bank_orders'")).fetchall()
    for c in cols:
        print(f"  {c[0]}: {c[1]}")
except Exception as e:
    print(f"  Error: {e}")

# Check tiers table
print("\n=== TIERS TABLE ===")
try:
    cols = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='tiers'")).fetchall()
    for c in cols:
        print(f"  {c[0]}: {c[1]}")
except Exception as e:
    print(f"  Error: {e}")

# Check products table
print("\n=== PRODUCTS TABLE ===")
try:
    cols = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='products'")).fetchall()
    for c in cols:
        print(f"  {c[0]}: {c[1]}")
except Exception as e:
    print(f"  Error: {e}")
