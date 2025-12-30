#!/usr/bin/env python3
"""Manually complete a bank order for testing"""

trans_code = "AFKPRO2251230002"

with open('/app/manual_complete.py', 'w') as f:
    f.write(f'''
import psycopg2
import secrets
from datetime import datetime, timedelta

conn = psycopg2.connect(
    host="db",
    database="afkzone_license",
    user="postgres",
    password="your_secure_password"
)

cur = conn.cursor()

# Get order
cur.execute("SELECT * FROM bank_orders WHERE trans_code=%s", ("{trans_code}",))
order = cur.fetchone()

if not order:
    print("❌ Order not found!")
    exit(1)

trans_code, device_id, _, tier, duration_days, amount = order[0], order[1], order[2], order[3], order[4], order[5]

print(f"📦 Order: {{trans_code}}")
print(f"  Device: {{device_id[:20]}}...")
print(f"  Product: {{tier}} - {{duration_days}} days - {{amount:,}}đ")

# Generate license key
license_key = f"AFK-{{secrets.token_hex(16).upper()}}"
print(f"🔑 Generated license: {{license_key}}")

# Create license
expires_at = datetime.now() + timedelta(days=duration_days)
cur.execute("""
    INSERT INTO licenses (license_key, tier, duration_days, max_devices, expires_at, is_active, created_at)
    VALUES (%s, %s, %s, %s, %s, TRUE, NOW())
    RETURNING id
""", (license_key, tier, duration_days, 5 if tier == 'basic' else -1, expires_at))

license_id = cur.fetchone()[0]
print(f"✅ License created: ID={{license_id}}")

# Activate license for device
cur.execute("""
    INSERT INTO license_devices (license_id, device_id, activated_at)
    VALUES (%s, %s, NOW())
""", (license_id, device_id))
print(f"✅ License activated for device")

# Update order status
cur.execute("""
    UPDATE bank_orders 
    SET status='success', license_key=%s, paid_at=NOW()
    WHERE trans_code=%s
""", (license_key, trans_code))
print(f"✅ Order marked as success")

conn.commit()
cur.close()
conn.close()

print(f"\\n🎉 Order completed! License: {{license_key}}")
''')

print("Script created. Running...")

