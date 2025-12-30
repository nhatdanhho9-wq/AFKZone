#!/usr/bin/env python3
"""
Script to add purchase history and license recovery endpoints to app.py
"""

NEW_ENDPOINTS = '''

# ==================== USER HISTORY ENDPOINTS ====================

@app.get("/user/history")
async def get_user_history(device_id: str = None, fingerprint: str = None, db: Session = Depends(get_db)):
    """Get purchase history for a device"""
    try:
        query = text("""
            SELECT DISTINCT l.license_key, l.tier, l.duration_days, l.expires_at, l.status,
                   CASE WHEN l.expires_at > NOW() THEN 'active' ELSE 'expired' END as current_status
            FROM licenses l
            LEFT JOIN license_devices ld ON l.license_key = ld.license_key
            WHERE ld.device_id = :device_id OR l.device_id = :device_id
            ORDER BY l.created_at DESC
            LIMIT 20
        """)
        result = db.execute(query, {"device_id": device_id})
        licenses = []
        for row in result:
            licenses.append({
                "license_key": row[0],
                "tier": row[1],
                "duration_days": row[2],
                "expires_at": row[3].strftime("%d/%m/%Y %H:%M") if row[3] else None,
                "status": row[5]
            })
        return {"licenses": licenses}
    except Exception as e:
        print(f"Error getting user history: {e}")
        return {"licenses": []}


@app.post("/license/recover")
async def recover_license(data: dict, db: Session = Depends(get_db)):
    """Recover license by transaction code"""
    trans_code = data.get("trans_code", "").strip().upper()
    
    if not trans_code:
        raise HTTPException(status_code=400, detail="Transaction code is required")
    
    try:
        query = text("""
            SELECT license_key, tier, duration_days, status
            FROM bank_orders
            WHERE trans_code = :trans_code
        """)
        result = db.execute(query, {"trans_code": trans_code}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Khong tim thay giao dich voi ma nay")
        
        license_key = result[0]
        status = result[3]
        
        if status != 'completed':
            raise HTTPException(status_code=400, detail="Giao dich chua duoc thanh toan hoan tat")
        
        if not license_key:
            raise HTTPException(status_code=400, detail="Giao dich chua co license, vui long lien he admin")
        
        license_query = text("""
            SELECT license_key, tier, duration_days, expires_at
            FROM licenses
            WHERE license_key = :license_key
        """)
        license_result = db.execute(license_query, {"license_key": license_key}).fetchone()
        
        if license_result:
            return {
                "license_key": license_result[0],
                "tier": license_result[1],
                "duration_days": license_result[2],
                "expires_at": license_result[3].strftime("%d/%m/%Y %H:%M") if license_result[3] else None
            }
        
        return {"license_key": license_key}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error recovering license: {e}")
        raise HTTPException(status_code=500, detail="Loi he thong, vui long thu lai")


@app.get("/admin/licenses/all")
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
        """)
        result = db.execute(query)
        licenses = []
        for row in result:
            from datetime import datetime as dt
            licenses.append({
                "license_key": row[0],
                "tier": row[1],
                "duration_days": row[2],
                "max_devices": row[3],
                "expires_at": row[4].strftime("%H:%M:%S %d/%m/%Y") if row[4] else None,
                "created_at": row[5].strftime("%H:%M:%S %d/%m/%Y") if row[5] else None,
                "status": "active" if row[4] and row[4] > dt.now() else "expired",
                "source": row[7],
                "device_count": row[8] or 0
            })
        return {"licenses": licenses}
    except Exception as e:
        print(f"Error getting all licenses: {e}")
        db.rollback()
        return {"licenses": []}


@app.get("/admin/devices/detailed")
async def get_detailed_devices(token: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Get devices with detailed info"""
    try:
        query = text("""
            SELECT ld.device_id, ld.license_key, ld.activated_at,
                   l.tier, l.expires_at
            FROM license_devices ld
            JOIN licenses l ON l.license_key = ld.license_key
            ORDER BY ld.activated_at DESC
            LIMIT 100
        """)
        result = db.execute(query)
        devices = []
        for row in result:
            devices.append({
                "device_id": row[0],
                "license_key": row[1],
                "activated_at": row[2].strftime("%H:%M:%S %d/%m/%Y") if row[2] else None,
                "tier": row[3],
                "expires_at": row[4].strftime("%d/%m/%Y") if row[4] else None
            })
        return {"devices": devices}
    except Exception as e:
        print(f"Error getting detailed devices: {e}")
        db.rollback()
        return {"devices": []}

'''

def main():
    print("Adding new endpoints to app.py...")
    
    with open('/app/app.py', 'r') as f:
        content = f.read()
    
    if '/user/history' in content:
        print("Endpoints already exist, skipping...")
        return
    
    content = content.rstrip() + NEW_ENDPOINTS
    
    with open('/app/app.py', 'w') as f:
        f.write(content)
    
    print("Endpoints added successfully!")

if __name__ == "__main__":
    main()
