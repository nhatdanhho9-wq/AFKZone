#!/usr/bin/env python3
"""Fix database: clear orders and reset product ID sequence"""
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Count current data
    orders_count = conn.execute(text("SELECT COUNT(*) FROM orders")).fetchone()[0]
    products_count = conn.execute(text("SELECT COUNT(*) FROM products")).fetchone()[0]
    licenses_count = conn.execute(text("SELECT COUNT(*) FROM licenses")).fetchone()[0]
    
    print(f"📊 Current data:")
    print(f"   - Orders: {orders_count}")
    print(f"   - Products: {products_count}")
    print(f"   - Licenses: {licenses_count}")
    
    # Clear orders
    conn.execute(text("DELETE FROM orders"))
    print("✅ Orders cleared!")
    
    # Clear licenses
    conn.execute(text("DELETE FROM licenses"))
    print("✅ Licenses cleared!")
    
    # Clear products
    conn.execute(text("DELETE FROM products"))
    print("✅ Products cleared!")
    
    # Reset product ID sequence to start from 1
    conn.execute(text("ALTER SEQUENCE products_id_seq RESTART WITH 1"))
    print("✅ Product ID sequence reset to 1!")
    
    # Reset license ID sequence if exists
    try:
        conn.execute(text("ALTER SEQUENCE licenses_id_seq RESTART WITH 1"))
        print("✅ License ID sequence reset to 1!")
    except:
        pass
    
    conn.commit()
    print("\n🎉 All done! Database is clean and ready.")
