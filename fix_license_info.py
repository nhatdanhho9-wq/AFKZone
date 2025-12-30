#!/usr/bin/env python3
"""Fix /license/info endpoint to use correct column"""

def main():
    with open('/app/app.py', 'r') as f:
        content = f.read()
    
    # Find and fix the incorrect query
    old_query = 'SELECT COUNT(*) FROM license_devices WHERE license_id = %(lid)s'
    new_query = 'SELECT COUNT(*) FROM license_devices WHERE license_key = :key'
    
    # Also fix the pattern with :lid
    content = content.replace('license_id = :lid', 'license_key = :key')
    content = content.replace('"lid":', '"key":')
    content = content.replace("'lid':", "'key':")
    content = content.replace('{"lid":', '{"key":')
    
    # More specific fix
    old_pattern = '''device_count = db.execute(
        text("SELECT COUNT(*) FROM license_devices WHERE license_id = :lid"),
        {"lid": license_id}
    ).scalar()'''
    
    new_pattern = '''device_count = db.execute(
        text("SELECT COUNT(*) FROM license_devices WHERE license_key = :key"),
        {"key": license_key}
    ).scalar()'''
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        print("Fixed device count query pattern 1")
    
    # Alternative pattern
    old_pattern2 = 'WHERE license_id ='
    new_pattern2 = 'WHERE license_key ='
    
    count = content.count(old_pattern2)
    if count > 0:
        content = content.replace(old_pattern2, new_pattern2)
        print(f"Fixed {count} occurrences of license_id")
    
    with open('/app/app.py', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()

