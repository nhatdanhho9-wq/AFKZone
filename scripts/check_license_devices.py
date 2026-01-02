#!/usr/bin/env python3
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:Afkzone123!@db:5432/license_db')
engine = create_engine(DATABASE_URL)

# Check license AFK-3E3B173BD9601E399E072E00E1508C99
with engine.connect() as conn:
    result = conn.execute(text("SELECT license_key, tier, max_devices FROM licenses WHERE license_key = 'AFK-3E3B173BD9601E399E072E00E1508C99'"))
    for row in result:
        print(f'License: {row[0]}, Tier: {row[1]}, Max Devices: {row[2]}')
    
    # Check devices
    result2 = conn.execute(text("SELECT device_id FROM license_devices WHERE license_key = 'AFK-3E3B173BD9601E399E072E00E1508C99'"))
    print('\nDevices:')
    count = 0
    for row in result2:
        count += 1
        print(f'  {count}. {row[0]}')
    print(f'\nTotal devices: {count}')

