#!/usr/bin/env python3
"""Check bank orders status"""
import psycopg2
import os

conn = psycopg2.connect(
    host="localhost",
    database="afkzone_license",
    user="postgres",
    password=os.getenv("DB_PASSWORD", "your_secure_password")
)

cur = conn.cursor()

print("=== Recent Bank Orders ===")
cur.execute("""
    SELECT trans_code, device_id, tier, duration_days, amount, status, license_key, 
           created_at, paid_at
    FROM bank_orders 
    ORDER BY created_at DESC 
    LIMIT 10
""")

for row in cur.fetchall():
    print(f"\nTrans: {row[0]}")
    print(f"  Device: {row[1][:20]}...")
    print(f"  Product: {row[2]} - {row[3]} days - {row[4]:,}đ")
    print(f"  Status: {row[5]}")
    print(f"  License: {row[6] or 'N/A'}")
    print(f"  Created: {row[7]}")
    print(f"  Paid: {row[8] or 'N/A'}")

cur.close()
conn.close()

