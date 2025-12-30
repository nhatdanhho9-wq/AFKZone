#!/usr/bin/env python3
"""Fix the /admin/licenses/all endpoint query"""

def main():
    with open('/app/app.py', 'r') as f:
        content = f.read()
    
    # Find and replace the broken query
    old_query = '''@app.get("/admin/licenses/all")
async def get_all_licenses_v2(token: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Get ALL licenses (both manual and from payments)"""
    try:
        query = text("""
            SELECT l.license_key, l.tier, l.duration_days, l.max_devices, l.expires_at, 
                   l.created_at, l.status,
                   COALESCE(bo.trans_code, 'manual') as source,
                   (SELECT COUNT(*) FROM license_devices ld WHERE ld.license_key = l.license_key) as device_count
            FROM licenses l
            LEFT JOIN bank_orders bo ON bo.license_key = l.license_key
            ORDER BY l.created_at DESC
            LIMIT 100
        """)'''
    
    new_query = '''@app.get("/admin/licenses/all")
async def get_all_licenses_v2(token: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Get ALL licenses (both manual and from payments)"""
    try:
        query = text("""
            SELECT l.license_key, l.tier, l.duration_days, l.max_devices, l.expires_at, 
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
        print("Fixed query (status -> is_revoked)")
    else:
        print("Query pattern not found, trying alternative fix...")
        # Try simpler fix
        content = content.replace("l.status,", "l.is_revoked,")
    
    # Also fix the result parsing
    old_parse = '''            licenses.append({
                "license_key": row[0],
                "tier": row[1],
                "duration_days": row[2],
                "max_devices": row[3],
                "expires_at": row[4].strftime("%H:%M:%S %d/%m/%Y") if row[4] else None,
                "created_at": row[5].strftime("%H:%M:%S %d/%m/%Y") if row[5] else None,
                "status": "active" if row[4] and row[4] > dt.now() else "expired",
                "source": row[7],
                "device_count": row[8] or 0
            })'''
    
    new_parse = '''            is_revoked = row[6] if row[6] else False
            is_expired = row[4] and row[4] < dt.now() if row[4] else False
            status = "revoked" if is_revoked else ("expired" if is_expired else "active")
            licenses.append({
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
    
    if old_parse in content:
        content = content.replace(old_parse, new_parse)
        print("Fixed result parsing")
    
    with open('/app/app.py', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()

