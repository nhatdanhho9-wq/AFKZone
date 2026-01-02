#!/usr/bin/env python3
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:Afkzone123!@db:5432/license_db')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Get column names
    result = conn.execute(text("""
        SELECT column_name, ordinal_position 
        FROM information_schema.columns 
        WHERE table_name = 'bank_orders' 
        ORDER BY ordinal_position
    """))
    print("bank_orders columns:")
    for row in result:
        print(f"  [{row[1]-1}]: {row[0]}")
    
    # Check specific order
    print("\nOrder AFKPRO90251231005:")
    result2 = conn.execute(text("SELECT * FROM bank_orders WHERE trans_code = 'AFKPRO90251231005' LIMIT 1"))
    row = result2.fetchone()
    if row:
        for i, val in enumerate(row):
            print(f"  [{i}]: {val}")

