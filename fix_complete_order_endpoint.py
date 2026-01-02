#!/usr/bin/env python3
"""Fix complete order endpoint to use old schema"""

with open('/app/app.py', 'r') as f:
    content = f.read()

# Find the manual complete endpoint
old_complete = '''    # Create license
    expires_at = datetime.now() + timedelta(days=duration_days)
    max_devices = 5 if tier == 'basic' else -1
    
    result = db.execute(text("""
        INSERT INTO licenses (license_key, tier, duration_days, max_devices, expires_at, is_active, created_at)
        VALUES (:key, :tier, :days, :max, :exp, TRUE, NOW())
        RETURNING id
    """), {"key": license_key, "tier": tier, "days": duration_days, "max": max_devices, "exp": expires_at})
    
    license_id = result.fetchone()[0]
    
    # Activate license for device
    db.execute(text("""
        INSERT INTO license_devices (license_id, device_id, activated_at)
        VALUES (:lid, :did, NOW())
    """), {"lid": license_id, "did": device_id})'''

new_complete = '''    # Create license with device_id (old schema)
    expires_at = datetime.now() + timedelta(days=duration_days)
    
    db.execute(text("""
        INSERT INTO licenses (license_key, tier, duration_days, activated_at, expires_at, device_id, created_at, is_trial, last_check)
        VALUES (:key, :tier, :dur, NOW(), :exp, :dev, NOW(), FALSE, NOW())
    """), {"key": license_key, "tier": tier, "dur": duration_days, "exp": expires_at, "dev": device_id})'''

if old_complete in content:
    content = content.replace(old_complete, new_complete)
    print("✅ Fixed manual complete endpoint")
else:
    print("❌ Code not found")

with open('/app/app.py', 'w') as f:
    f.write(content)

import ast
try:
    ast.parse(content)
    print('✅ Syntax valid')
except SyntaxError as e:
    print(f'❌ Syntax error: {e}')

