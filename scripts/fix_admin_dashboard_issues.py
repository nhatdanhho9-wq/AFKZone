#!/usr/bin/env python3
"""Fix admin dashboard issues:
1. Add activated_at to licenses/all endpoint
2. Fix activation display logic
3. Improve device info display
"""

def main():
    with open('/app/app.py', 'r') as f:
        content = f.read()
    
    # Fix 1: Add activated_at to licenses/all endpoint
    old_query = '''query = text("""
            SELECT l.license_key, l.tier, l.duration_days, l.max_devices, l.expires_at, 
                   l.created_at, l.is_revoked,
                   COALESCE(bo.trans_code, 'manual') as source,
                   (SELECT COUNT(*) FROM license_devices ld WHERE ld.license_key = l.license_key) as device_count
            FROM licenses l
            LEFT JOIN bank_orders bo ON bo.license_key = l.license_key
            ORDER BY l.created_at DESC
            LIMIT 100
        """)'''
    
    new_query = '''query = text("""
            SELECT l.license_key, l.tier, l.duration_days, l.max_devices, l.activated_at, l.expires_at, 
                   l.created_at, l.is_revoked,
                   COALESCE(bo.trans_code, 'manual') as source,
                   (SELECT COUNT(*) FROM license_devices ld WHERE ld.license_key = l.license_key) as device_count
            FROM licenses l
            LEFT JOIN bank_orders bo ON bo.license_key = l.license_key
            ORDER BY l.created_at DESC
            LIMIT 100
        """)'''
    
    if old_query in content:
        content = content.replace(old_query, new_query)
        print("Fixed query to include activated_at")
    
    # Fix 2: Update response to include activated_at
    old_response = '''licenses.append({
                "license_key": row[0],
                "tier": row[1],
                "duration_days": row[2],
                "max_devices": row[3],
                "expires_at": row[4].strftime("%H:%M:%S %d/%m/%Y") if row[4] else None,
                "created_at": row[5].strftime("%H:%M:%S %d/%m/%Y") if row[5] else None,
                "status": status,
                "source": row[7],
                "device_count": row[8] or 0
            })'''
    
    new_response = '''licenses.append({
                "license_key": row[0],
                "tier": row[1],
                "duration_days": row[2],
                "max_devices": row[3],
                "activated_at": row[4].strftime("%H:%M:%S %d/%m/%Y") if row[4] else None,
                "expires_at": row[5].strftime("%H:%M:%S %d/%m/%Y") if row[5] else None,
                "created_at": row[6].strftime("%H:%M:%S %d/%m/%Y") if row[6] else None,
                "status": status,
                "source": row[8],
                "device_count": row[9] or 0
            })'''
    
    if old_response in content:
        content = content.replace(old_response, new_response)
        print("Fixed response to include activated_at")
    
    # Fix 3: Update is_revoked and is_expired logic
    old_logic = '''is_revoked = row[6] if row[6] else False
            is_expired = row[4] and row[4] < dt.now() if row[4] else False'''
    
    new_logic = '''is_revoked = row[7] if row[7] else False
            is_expired = row[5] and row[5] < dt.now() if row[5] else False'''
    
    if old_logic in content:
        content = content.replace(old_logic, new_logic)
        print("Fixed is_revoked and is_expired logic")
    
    with open('/app/app.py', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()

