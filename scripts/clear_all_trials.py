#!/usr/bin/env python3
"""Clear all trial devices and licenses for re-testing"""
import sys
sys.path.append("/app")
from database import get_db
from sqlalchemy import text

db = next(get_db())

# Count before deletion
trial_devices_count = db.execute(text("SELECT COUNT(*) FROM trial_devices")).scalar()
license_devices_trial_count = db.execute(text("""
    SELECT COUNT(*) FROM license_devices 
    WHERE license_key LIKE 'AFK-TRIAL-%'
""")).scalar()
trial_licenses_count = db.execute(text("SELECT COUNT(*) FROM licenses WHERE is_trial=TRUE")).scalar()

print(f"=== Before Deletion ===")
print(f"Trial devices: {trial_devices_count}")
print(f"License devices (trial): {license_devices_trial_count}")
print(f"Trial licenses: {trial_licenses_count}")

# Delete all trial devices
print("\n=== Deleting Trial Devices ===")
result = db.execute(text("DELETE FROM trial_devices"))
print(f"Deleted trial devices")

# Delete license_devices entries for trial licenses
print("\n=== Deleting License Devices (Trial) ===")
db.execute(text("DELETE FROM license_devices WHERE license_key LIKE 'AFK-TRIAL-%'"))
print(f"Deleted license devices for trial licenses")

# Delete trial licenses from licenses table
print("\n=== Deleting Trial Licenses ===")
db.execute(text("DELETE FROM licenses WHERE is_trial=TRUE"))
print(f"Deleted trial licenses")

# Commit all changes
db.commit()

# Verify deletion
trial_devices_after = db.execute(text("SELECT COUNT(*) FROM trial_devices")).scalar()
license_devices_trial_after = db.execute(text("""
    SELECT COUNT(*) FROM license_devices 
    WHERE license_key LIKE 'AFK-TRIAL-%'
""")).scalar()
trial_licenses_after = db.execute(text("SELECT COUNT(*) FROM licenses WHERE is_trial=TRUE")).scalar()

print(f"\n=== After Deletion ===")
print(f"Trial devices: {trial_devices_after}")
print(f"License devices (trial): {license_devices_trial_after}")
print(f"Trial licenses: {trial_licenses_after}")

print("\n✅ All trial data cleared successfully!")

