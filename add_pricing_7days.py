#!/usr/bin/env python3
"""Add 7-day basic paid to pricing table"""
import sys
sys.path.append("/app")
from database import get_db
from sqlalchemy import text

db = next(get_db())

# Check if exists
existing = db.execute(text("SELECT tier, duration_days, price FROM pricing WHERE tier='basic' AND duration_days=7")).fetchone()
if existing:
    print(f"Already exists: tier={existing[0]}, days={existing[1]}, price={existing[2]}")
    if existing[2] != 15000:
        # Update price
        db.execute(text("UPDATE pricing SET price=15000 WHERE tier='basic' AND duration_days=7"))
        db.commit()
        print("Updated price to 15000")
else:
    # Insert new
    db.execute(text("INSERT INTO pricing (tier, duration_days, price) VALUES ('basic', 7, 15000)"))
    db.commit()
    print("Added: basic 7 days = 15000")

# Verify
result = db.execute(text("SELECT tier, duration_days, price FROM pricing WHERE tier='basic' AND duration_days=7")).fetchone()
print(f"Verified: tier={result[0]}, days={result[1]}, price={result[2]}")

