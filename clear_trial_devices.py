#!/usr/bin/env python3
"""Clear all trial devices from database"""
import sys
sys.path.append("/app")
from database import get_db
from sqlalchemy import text

db = next(get_db())

# Count before delete
count_before = db.execute(text("SELECT COUNT(*) FROM trial_devices")).fetchone()[0]
print(f"Found {count_before} trial devices")

# Delete all trial devices
db.execute(text("DELETE FROM trial_devices"))
db.commit()

# Verify
count_after = db.execute(text("SELECT COUNT(*) FROM trial_devices")).fetchone()[0]
print(f"Deleted {count_before} trial devices")
print(f"Remaining: {count_after}")

# Also delete trial licenses (optional - comment out if you want to keep licenses)
trial_licenses = db.execute(text("SELECT COUNT(*) FROM licenses WHERE is_trial=TRUE")).fetchone()[0]
print(f"\nFound {trial_licenses} trial licenses")
print("Note: Trial licenses are kept in licenses table. Delete manually if needed:")
print("  DELETE FROM licenses WHERE is_trial=TRUE;")

