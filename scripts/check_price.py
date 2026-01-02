#!/usr/bin/env python3
"""Check product price on server"""
import sys
sys.path.append("/app")
from database import get_db
from sqlalchemy import text

db = next(get_db())
result = db.execute(text("SELECT id, tier, duration_days, price FROM products WHERE tier='basic' AND duration_days=7")).fetchone()
if result:
    print(f"ID={result[0]}, Tier={result[1]}, Days={result[2]}, Price={result[3]}")
else:
    print("Product not found!")
