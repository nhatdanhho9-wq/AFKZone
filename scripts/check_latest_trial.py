#!/usr/bin/env python3
"""Check latest trial activation attempts"""
import sys
sys.path.append("/app")
from database import get_db
from sqlalchemy import text

db = next(get_db())

print("=== Latest Trial Devices (Last 5) ===")
trial_devices = db.execute(text("""
    SELECT device_fingerprint, license_key, created_at 
    FROM trial_devices 
    ORDER BY created_at DESC 
    LIMIT 5
""")).fetchall()
for td in trial_devices:
    print(f"Device: {td[0][:30]}..., License: {td[1]}, Created: {td[2]}")

print("\n=== Latest Trial Licenses (Last 5) ===")
trial_licenses = db.execute(text("""
    SELECT license_key, device_fingerprint, activated_at, expires_at 
    FROM licenses 
    WHERE is_trial=TRUE 
    ORDER BY created_at DESC 
    LIMIT 5
""")).fetchall()
for tl in trial_licenses:
    print(f"License: {tl[0]}, Device: {tl[1][:30] if tl[1] else 'None'}..., Activated: {tl[2]}, Expires: {tl[3]}")

print("\n=== Latest License Devices Activations (Last 5) ===")
license_devices = db.execute(text("""
    SELECT license_key, device_id, activated_at 
    FROM license_devices 
    WHERE license_key LIKE 'AFK-TRIAL-%'
    ORDER BY activated_at DESC 
    LIMIT 5
""")).fetchall()
for ld in license_devices:
    print(f"License: {ld[0]}, Device: {ld[1][:30]}..., Activated: {ld[2]}")

