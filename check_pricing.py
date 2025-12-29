#!/usr/bin/env python3
"""Check pricing table for 7-day basic"""
import sys
sys.path.append("/app")
from database import get_db
from sqlalchemy import text

db = next(get_db())
# Check pricing table
result = db.execute(text("SELECT tier, duration_days, price FROM pricing WHERE tier='basic' AND duration_days=7")).fetchone()
if result:
    print(f"Found in pricing: tier={result[0]}, days={result[1]}, price={result[2]}")
else:
    print("NOT FOUND in pricing table - need to add!")
    # Check products table
    prod_result = db.execute(text("SELECT tier, duration_days, price FROM products WHERE tier='basic' AND duration_days=7")).fetchone()
    if prod_result:
        print(f"Found in products: tier={prod_result[0]}, days={prod_result[1]}, price={prod_result[2]}")
        print("Need to add to pricing table!")

