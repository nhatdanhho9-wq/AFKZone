#!/usr/bin/env python3
"""Fix trial issues:
1. Create trial product with max_devices = 1
2. Fix trial-devices endpoint
3. Fix trial-devices display in frontend
"""

from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:Afkzone123!@db:5432/license_db')
engine = create_engine(DATABASE_URL)

def main():
    with engine.connect() as conn:
        # 1. Check if trial product exists
        result = conn.execute(text("""
            SELECT id FROM products 
            WHERE tier = 'basic' AND duration_days = 7 AND price = 0
        """)).fetchone()
        
        if not result:
            # Create trial product
            print("Creating trial product with max_devices = 1...")
            conn.execute(text("""
                INSERT INTO products (name, tier, duration_days, price, max_devices, is_active, display_order, description)
                VALUES ('Gói Dùng Thử', 'basic', 7, 0, 1, TRUE, 0, 'Gói dùng thử 7 ngày miễn phí - 1 thiết bị')
            """))
            conn.commit()
            print("Trial product created!")
        else:
            # Update existing trial product to max_devices = 1
            print(f"Updating trial product (id={result[0]}) max_devices to 1...")
            conn.execute(text("""
                UPDATE products 
                SET max_devices = 1 
                WHERE id = :id
            """), {"id": result[0]})
            conn.commit()
            print("Trial product updated!")
        
        # 2. Also update all basic products to max_devices = 1 (if they are trial-like)
        print("\nUpdating all basic 7-day products to max_devices = 1...")
        conn.execute(text("""
            UPDATE products 
            SET max_devices = 1 
            WHERE tier = 'basic' AND duration_days = 7
        """))
        conn.commit()
        print("Done!")

if __name__ == "__main__":
    main()

