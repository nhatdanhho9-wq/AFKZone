#!/usr/bin/env python3
"""Fix webhook to use correct max_devices based on tier"""

def main():
    with open('/app/app.py', 'r') as f:
        content = f.read()
    
    # Fix the wrong logic in webhook
    old_code = "max_devices = 5 if tier == 'basic' else -1"
    new_code = "max_devices = get_max_devices_for_tier(tier)  # basic=2, pro=5, enterprise=-1"
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        print(f"Fixed webhook max_devices logic")
    else:
        print("Old pattern not found, checking alternatives...")
        # Try another pattern
        if "max_devices = 5 if tier ==" in content:
            print("Found partial pattern")
        
    # Also fix the license_devices insert that uses license_id instead of license_key
    old_insert = '''db.execute(text("""
                INSERT INTO license_devices (license_id, device_id, activated_at)
                VALUES (:lid, :did, NOW())
            """), {"key": license_id, "did": device_id})'''
    
    new_insert = '''db.execute(text("""
                INSERT INTO license_devices (license_key, device_id, activated_at)
                VALUES (:key, :did, NOW())
            """), {"key": license_key, "did": device_id})'''
    
    if old_insert in content:
        content = content.replace(old_insert, new_insert)
        print("Fixed license_devices insert")
    else:
        # Try simpler pattern
        content = content.replace(
            "INSERT INTO license_devices (license_id, device_id, activated_at)",
            "INSERT INTO license_devices (license_key, device_id, activated_at)"
        )
        content = content.replace(
            '{"key": license_id, "did": device_id}',
            '{"key": license_key, "did": device_id}'
        )
        print("Fixed with simple patterns")
    
    with open('/app/app.py', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()

