#!/usr/bin/env python3
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:Afkzone123!@db:5432/license_db')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check trial product (basic tier, 7 days, price 0)
    result = conn.execute(text("""
        SELECT id, name, tier, duration_days, price, max_devices, display_order
        FROM products 
        WHERE tier = 'basic' AND duration_days = 7 AND price = 0
        ORDER BY display_order
        LIMIT 1
    """))
    
    print('Trial product in products table:')
    for row in result:
        print(f'  ID: {row[0]}, Name: {row[1]}, Tier: {row[2]}, Duration: {row[3]} days, Price: {row[4]}, Max Devices: {row[5]}, Order: {row[6]}')
    
    # Check all basic products
    print('\nAll basic tier products:')
    result2 = conn.execute(text("""
        SELECT id, name, tier, duration_days, price, max_devices
        FROM products 
        WHERE tier = 'basic'
        ORDER BY duration_days, price
    """))
    for row in result2:
        print(f'  {row[3]} days - {row[4]}đ - Max Devices: {row[5]}')

