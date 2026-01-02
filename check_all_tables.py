#!/usr/bin/env python3
from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print('=== TRIAL DEVICES ===')
r = db.execute(text('SELECT * FROM trial_devices LIMIT 20'))
for row in r:
    print(row)

print()
print('=== LICENSE DEVICES ===')
r = db.execute(text('SELECT * FROM license_devices LIMIT 20'))
for row in r:
    print(row)

print()
print('=== LICENSES (first 10) ===')
r = db.execute(text('SELECT license_key, tier, status FROM licenses LIMIT 10'))
for row in r:
    print(row)

db.close()

