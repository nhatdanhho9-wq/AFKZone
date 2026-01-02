#!/usr/bin/env python3
"""Check recent trial devices and licenses"""
import sys
sys.path.append("/app")
from database import get_db
from sqlalchemy import text

db = next(get_db())

# Check recent trial devices
print("=== Recent Trial Devices ===")
trial_devices = db.execute(text("SELECT device_fingerprint, license_key, created_at FROM trial_devices ORDER BY created_at DESC LIMIT 10")).fetchall()
for td in trial_devices:
    print(f"Device: {td[0][:20]}..., License: {td[1]}, Created: {td[2]}")

print("\n=== Recent Trial Licenses ===")
trial_licenses = db.execute(text("SELECT license_key, device_fingerprint, activated_at, expires_at FROM licenses WHERE is_trial=TRUE ORDER BY created_at DESC LIMIT 10")).fetchall()
for tl in trial_licenses:
    print(f"License: {tl[0]}, Device: {tl[1][:20] if tl[1] else 'None'}..., Activated: {tl[2]}, Expires: {tl[3]}")

print("\n=== Recent License Devices (activations) ===")
license_devices = db.execute(text("SELECT license_key, device_id, activated_at FROM license_devices ORDER BY activated_at DESC LIMIT 10")).fetchall()
for ld in license_devices:
    print(f"License: {ld[0]}, Device: {ld[1][:20]}..., Activated: {ld[2]}")

