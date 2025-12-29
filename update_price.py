#!/usr/bin/env python3
"""Update product price on server"""
import sys
sys.path.append("/app")
from database import get_db
from sqlalchemy import text

db = next(get_db())
# Update price
db.execute(text("UPDATE products SET price = 15000 WHERE tier = 'basic' AND duration_days = 7"))
db.commit()

# Verify
result = db.execute(text("SELECT id, name, tier, duration_days, price FROM products WHERE tier='basic' AND duration_days=7")).fetchone()
if result:
    print(f"Updated: ID={result[0]}, Name={result[1]}, Tier={result[2]}, Days={result[3]}, Price={result[4]}")
else:
    print("Product not found!")
