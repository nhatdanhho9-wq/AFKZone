#!/usr/bin/env python3
"""Completely rewrite /license/info endpoint"""

NEW_ENDPOINT = '''
@app.get("/license/info")
def get_license_info(license_key: str, db: Session = Depends(get_db)):
    """Get license info including device count"""
    try:
        # Get license
        lic = db.execute(text("""
            SELECT id, license_key, tier, duration_days, activated_at, expires_at, max_devices, is_revoked
            FROM licenses WHERE license_key = :key
        """), {"key": license_key}).fetchone()
        
        if not lic:
            raise HTTPException(status_code=404, detail="License not found")
        
        # Get device count using license_key
        device_count = db.execute(
            text("SELECT COUNT(*) FROM license_devices WHERE license_key = :key"),
            {"key": license_key}
        ).scalar() or 0
        
        max_devices = lic[6] if lic[6] else 1
        
        return {
            "license_key": lic[1],
            "tier": lic[2],
            "duration_days": lic[3],
            "activated_at": lic[4].isoformat() if lic[4] else None,
            "expires_at": lic[5].isoformat() if lic[5] else None,
            "max_devices": max_devices,
            "device_count": device_count,
            "is_revoked": lic[7] if len(lic) > 7 else False,
            "devices_remaining": (max_devices - device_count) if max_devices != -1 else -1
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

'''

def main():
    with open('/app/app.py', 'r') as f:
        content = f.read()
    
    # Find and remove old /license/info endpoint
    start_marker = '@app.get("/license/info")'
    start_idx = content.find(start_marker)
    
    if start_idx > 0:
        # Find end of function
        end_markers = ['@app.get(', '@app.post(', '@app.put(', '@app.delete(']
        end_idx = len(content)
        
        for marker in end_markers:
            idx = content.find(marker, start_idx + len(start_marker))
            if idx > 0 and idx < end_idx:
                end_idx = idx
        
        # Remove old function and replace with new
        content = content[:start_idx] + NEW_ENDPOINT + '\n' + content[end_idx:]
        print("Replaced /license/info endpoint")
    else:
        # Add new endpoint
        content = content.rstrip() + NEW_ENDPOINT
        print("Added /license/info endpoint")
    
    with open('/app/app.py', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()

