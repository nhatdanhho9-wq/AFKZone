#!/usr/bin/env python3
"""
Fix /license/logout bug - wrong parameter in DELETE query
"""

def fix_logout_bug():
    with open('/app/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open('/app/app.py.bak_logout_fix', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Fix: DELETE query uses license_key (STRING) but passes license_id (INT)
    old_delete = '''        # Remove device from license_devices
        db.execute(
            text("DELETE FROM license_devices WHERE license_key = :key AND device_id = :did"),
            {"key": license_id, "did": request.device_id}
        )'''
    
    new_delete = '''        # Remove device from license_devices
        db.execute(
            text("DELETE FROM license_devices WHERE license_key = :key AND device_id = :did"),
            {"key": request.license_key, "did": request.device_id}
        )'''
    
    if old_delete in content:
        content = content.replace(old_delete, new_delete)
        print("✅ Fixed /license/logout DELETE query")
    else:
        print("⚠️ Pattern not found - may already be fixed")
    
    # Write back
    with open('/app/app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ Logout bug fixed!")
    print("   Changed: license_id → request.license_key")
    print("   Restart API to apply changes")

if __name__ == '__main__':
    fix_logout_bug()
