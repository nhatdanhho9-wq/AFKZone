#!/usr/bin/env python3
from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres:Afkzone123!@db:5432/license_db')
with engine.connect() as conn:
    result = conn.execute(text("SELECT license_key, tier, max_devices FROM licenses WHERE license_key = 'AFK-9FBE1B13A6C651854D05F255C402504F'"))
    for row in result:
        print(f'License: {row[0]}, Tier: {row[1]}, Max Devices: {row[2]}')

