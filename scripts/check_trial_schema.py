#!/usr/bin/env python3
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:Afkzone123!@db:5432/license_db')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check trial_devices schema
    result = conn.execute(text("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'trial_devices' 
        ORDER BY ordinal_position
    """))
    print('trial_devices columns:')
    for row in result:
        print(f'  - {row[0]}: {row[1]}')
    
    # Check actual data
    print('\nActual data:')
    result2 = conn.execute(text('SELECT * FROM trial_devices LIMIT 1'))
    for row in result2:
        print(f'  Row: {row}')

