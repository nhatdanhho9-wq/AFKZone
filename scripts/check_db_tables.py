#!/usr/bin/env python3
"""
Check database tables and fix Casso webhook
"""

from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://afkzone:afkzone@localhost/afkzone")

def check_tables():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # List all tables
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"))
        print("=== TABLES IN DATABASE ===")
        for row in result:
            print(f"  - {row[0]}")
        
        # Check orders table
        print("\n=== ORDERS TABLE STRUCTURE ===")
        try:
            result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='orders' ORDER BY ordinal_position"))
            for row in result:
                print(f"  {row[0]}: {row[1]}")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Check payments table
        print("\n=== PAYMENTS TABLE STRUCTURE ===")
        try:
            result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='payments' ORDER BY ordinal_position"))
            cols = list(result)
            if cols:
                for row in cols:
                    print(f"  {row[0]}: {row[1]}")
            else:
                print("  Table does not exist!")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Check recent orders
        print("\n=== RECENT ORDERS (last 5) ===")
        try:
            result = conn.execute(text("SELECT order_id, device_id, tier, payment_status, created_at FROM orders ORDER BY id DESC LIMIT 5"))
            for row in result:
                print(f"  {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == '__main__':
    check_tables()
