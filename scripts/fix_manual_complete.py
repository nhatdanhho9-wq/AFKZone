#!/usr/bin/env python3
"""Fix manual complete to use max_devices and license_devices table"""

def main():
    with open('/app/app.py', 'r') as f:
        content = f.read()
    
    # Find and replace the manual complete function's license creation
    old_insert = '''db.execute(text("""
        INSERT INTO licenses (license_key, tier, duration_days, activated_at, expires_at, device_id, created_at, is_trial, last_check)
        VALUES (:key, :tier, :dur, NOW(), :exp, :dev, NOW(), FALSE, NOW())
    """), {"key": license_key, "tier": tier, "dur": duration_days, "exp": expires_at, "dev": device_id})'''
    
    new_insert = '''# Get max_devices for tier
    max_devices = get_max_devices_for_tier(tier)
    
    db.execute(text("""
        INSERT INTO licenses (license_key, tier, duration_days, max_devices, activated_at, expires_at, is_active, created_at)
        VALUES (:key, :tier, :dur, :max, NOW(), :exp, TRUE, NOW())
    """), {"key": license_key, "tier": tier, "dur": duration_days, "max": max_devices, "exp": expires_at})
    
    # Add device to license_devices
    db.execute(text("""
        INSERT INTO license_devices (license_key, device_id, activated_at)
        VALUES (:key, :dev, NOW())
    """), {"key": license_key, "dev": device_id})'''
    
    if old_insert in content:
        content = content.replace(old_insert, new_insert)
        print("Fixed manual complete license creation")
    else:
        print("Old pattern not found, trying alternatives...")
        
        # Try simpler pattern
        if "device_id, created_at, is_trial, last_check" in content:
            content = content.replace(
                "INSERT INTO licenses (license_key, tier, duration_days, activated_at, expires_at, device_id, created_at, is_trial, last_check)",
                "INSERT INTO licenses (license_key, tier, duration_days, max_devices, activated_at, expires_at, is_active, created_at)"
            )
            content = content.replace(
                "VALUES (:key, :tier, :dur, NOW(), :exp, :dev, NOW(), FALSE, NOW())",
                "VALUES (:key, :tier, :dur, get_max_devices_for_tier(:tier), NOW(), :exp, TRUE, NOW())"
            )
            print("Applied alternative fix")
    
    with open('/app/app.py', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()

