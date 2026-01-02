#!/usr/bin/env python3
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:Afkzone123!@db:5432/license_db')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check trial license max_devices
    result = conn.execute(text("SELECT license_key, tier, max_devices FROM licenses WHERE license_key LIKE 'AFK-TRIAL-%' LIMIT 1"))
    for row in result:
        print(f'Trial license: {row[0]}, tier: {row[1]}, max_devices: {row[2]}')
    
    # Check trial_devices table
    count = conn.execute(text('SELECT COUNT(*) FROM trial_devices')).scalar()
    print(f'\nTrial devices count: {count}')
    
    # List trial devices
    if count > 0:
        result2 = conn.execute(text('SELECT device_id, license_key, used_at FROM trial_devices LIMIT 5'))
        print('\nTrial devices:')
        for row in result2:
            print(f'  - device_id: {row[0][:50]}..., license: {row[1]}, used_at: {row[2]}')

