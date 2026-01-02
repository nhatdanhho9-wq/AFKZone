#!/usr/bin/env python3
from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

print('=== LICENSES TABLE COLUMNS ===')
r = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'licenses'"))
for row in r:
    print(f"  {row[0]}")

print()
print('=== LICENSES DATA ===')
r = db.execute(text('SELECT * FROM licenses LIMIT 5'))
for row in r:
    print(row)

db.close()

