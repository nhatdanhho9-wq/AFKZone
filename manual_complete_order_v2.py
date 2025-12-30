#!/usr/bin/env python3
"""Manually complete a bank order for testing - using SQLAlchemy"""

trans_code = "AFKPRO2251230002"

code = f'''
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import secrets

engine = create_engine("postgresql://postgres:your_secure_password@db:5432/afkzone_license")

with engine.connect() as conn:
    # Get order
    result = conn.execute(text("SELECT * FROM bank_orders WHERE trans_code=:code"), {{"code": "{trans_code}"}})
    order = result.fetchone()
    
    if not order:
        print("❌ Order not found!")
        exit(1)
    
    trans_code, device_id, tier, duration_days, amount = order[0], order[1], order[3], order[4], order[5]
    
    print(f"📦 Order: {{trans_code}}")
    print(f"  Device: {{device_id[:20]}}...")
    print(f"  Product: {{tier}} - {{duration_days}} days - {{amount:,}}đ")
    
    # Generate license key
    license_key = f"AFK-{{secrets.token_hex(16).upper()}}"
    print(f"🔑 Generated license: {{license_key}}")
    
    # Create license
    expires_at = datetime.now() + timedelta(days=duration_days)
    max_devices = 5 if tier == 'basic' else -1
    
    result = conn.execute(text("""
        INSERT INTO licenses (license_key, tier, duration_days, max_devices, expires_at, is_active, created_at)
        VALUES (:key, :tier, :days, :max, :exp, TRUE, NOW())
        RETURNING id
    """), {{"key": license_key, "tier": tier, "days": duration_days, "max": max_devices, "exp": expires_at}})
    
    license_id = result.fetchone()[0]
    print(f"✅ License created: ID={{license_id}}")
    
    # Activate license for device
    conn.execute(text("""
        INSERT INTO license_devices (license_id, device_id, activated_at)
        VALUES (:lid, :did, NOW())
    """), {{"lid": license_id, "did": device_id}})
    print(f"✅ License activated for device")
    
    # Update order status
    conn.execute(text("""
        UPDATE bank_orders 
        SET status='success', license_key=:key, paid_at=NOW()
        WHERE trans_code=:code
    """), {{"key": license_key, "code": trans_code}})
    print(f"✅ Order marked as success")
    
    conn.commit()
    
    print(f"\\n🎉 Order completed! License: {{license_key}}")
'''

print(code)

