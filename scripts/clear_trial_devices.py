#!/usr/bin/env python3
"""Clear all trial devices from database"""

from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:Afkzone123!@db:5432/license_db')
engine = create_engine(DATABASE_URL)

def clear_trial_devices():
    with engine.connect() as conn:
        # Count before
        count_before = conn.execute(text("SELECT COUNT(*) FROM trial_devices")).scalar()
        print(f"Trial devices before: {count_before}")
        
        # Delete all trial devices
        result = conn.execute(text("DELETE FROM trial_devices"))
        conn.commit()
        
        # Count after
        count_after = conn.execute(text("SELECT COUNT(*) FROM trial_devices")).scalar()
        print(f"Trial devices after: {count_after}")
        print(f"Deleted: {count_before - count_after} trial devices")
        
        # Also delete trial licenses and license_devices
        print("\nCleaning up trial licenses...")
        trial_licenses = conn.execute(text("""
            SELECT license_key FROM licenses 
            WHERE license_key LIKE 'AFK-TRIAL-%'
        """)).fetchall()
        
        if trial_licenses:
            print(f"Found {len(trial_licenses)} trial licenses")
            for row in trial_licenses:
                license_key = row[0]
                # Delete license_devices
                conn.execute(text("DELETE FROM license_devices WHERE license_key = :key"), {"key": license_key})
                # Delete license
                conn.execute(text("DELETE FROM licenses WHERE license_key = :key"), {"key": license_key})
                print(f"  Deleted trial license: {license_key}")
            
            conn.commit()
            print("Trial licenses cleaned up!")
        else:
            print("No trial licenses found")

if __name__ == "__main__":
    clear_trial_devices()
