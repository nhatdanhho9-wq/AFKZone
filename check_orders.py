#!/usr/bin/env python3
from database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
r = db.execute(text("SELECT trans_code, status, license_key FROM bank_orders ORDER BY created_at DESC LIMIT 10"))
print("=== Bank Orders ===")
for row in r:
    print(f"  {row[0]} | {row[1]} | {row[2]}")
db.close()

