#!/usr/bin/env python3
"""Fix max_devices in licenses table based on tier"""

from sqlalchemy import create_engine, text
import os

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:Afkzone123!@db:5432/license_db')
engine = create_engine(DATABASE_URL)

# Tier to max_devices mapping
TIER_DEVICES = {
    'basic': 2,
    'pro': 5,
    'enterprise': -1  # unlimited
}

def fix_max_devices():
    with engine.connect() as conn:
        # Get all licenses with wrong max_devices
        result = conn.execute(text("SELECT license_key, tier, max_devices FROM licenses"))
        for row in result:
            license_key = row[0]
            tier = row[1]
            current_max = row[2]
            expected_max = TIER_DEVICES.get(tier, 1)
            
            if current_max != expected_max:
                print(f"Fixing {license_key}: tier={tier}, current={current_max}, expected={expected_max}")
                conn.execute(text(
                    "UPDATE licenses SET max_devices = :max WHERE license_key = :key"
                ), {"max": expected_max, "key": license_key})
        
        conn.commit()
        print("Done!")

if __name__ == "__main__":
    fix_max_devices()

