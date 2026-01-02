#!/usr/bin/env python3
"""Fix /activate endpoint to properly support multi-device"""

def main():
    with open('/app/app.py', 'r') as f:
        content = f.read()
    
    # Find and fix the activate endpoint
    # The issue is that it's checking device_id in license_devices incorrectly
    
    old_activate = '''@app.post("/activate")
def activate_license(data: dict, db: Session = Depends(get_db)):
    license_key = data.get("license_key")
    device_id = data.get("device_id")
    
    if not license_key or not device_id:
        raise HTTPException(status_code=400, detail="Missing license_key or device_id")
    
    # Check if license exists
    lic = db.execute(
        text("SELECT license_key, tier, duration_days, activated_at, expires_at, max_devices, is_revoked FROM licenses WHERE license_key=:key"),
        {"key": license_key}
    ).fetchone()
    
    if not lic:
        raise HTTPException(status_code=404, detail="License không hợp lệ")
    
    if lic[6]:  # is_revoked
        raise HTTPException(status_code=403, detail="License đã bị thu hồi")'''
    
    # Check if this pattern exists
    if old_activate not in content:
        print("Pattern not found, checking for alternative...")
        
        # Try to find activate endpoint
        if '@app.post("/activate")' in content:
            print("Found /activate endpoint, patching multi-device logic...")
            
            # Add a comprehensive fix
            fix_code = '''
# ==================== MULTI-DEVICE ACTIVATION FIX ====================
@app.post("/activate-v2")
def activate_license_v2(data: dict, db: Session = Depends(get_db)):
    """Activate license on a device - supports multi-device"""
    license_key = data.get("license_key")
    device_id = data.get("device_id")
    
    if not license_key or not device_id:
        raise HTTPException(status_code=400, detail="Missing license_key or device_id")
    
    # Check if license exists
    lic = db.execute(
        text("SELECT license_key, tier, duration_days, activated_at, expires_at, max_devices, is_revoked FROM licenses WHERE license_key=:key"),
        {"key": license_key}
    ).fetchone()
    
    if not lic:
        raise HTTPException(status_code=404, detail="License không hợp lệ")
    
    if lic[6]:  # is_revoked
        raise HTTPException(status_code=403, detail="License đã bị thu hồi")
    
    max_devices = lic[5] or 1
    
    # Check if device is already activated with this license
    existing = db.execute(
        text("SELECT id FROM license_devices WHERE license_key=:key AND device_id=:device"),
        {"key": license_key, "device": device_id}
    ).fetchone()
    
    if existing:
        # Device already activated - return success
        return {
            "status": "active",
            "tier": lic[1],
            "duration_days": lic[2],
            "expires_at": lic[4].isoformat() if lic[4] else None,
            "max_devices": max_devices,
            "message": "Device đã được kích hoạt trước đó"
        }
    
    # Count current activated devices
    device_count = db.execute(
        text("SELECT COUNT(*) FROM license_devices WHERE license_key=:key"),
        {"key": license_key}
    ).scalar() or 0
    
    # Check if max devices reached (skip check if max_devices = -1 = unlimited)
    if max_devices != -1 and device_count >= max_devices:
        raise HTTPException(
            status_code=400, 
            detail=f"License đã đạt giới hạn {max_devices} thiết bị. Vui lòng xóa thiết bị cũ hoặc nâng cấp gói."
        )
    
    # Activate on this device
    db.execute(
        text("INSERT INTO license_devices (license_key, device_id, activated_at) VALUES (:key, :device, NOW())"),
        {"key": license_key, "device": device_id}
    )
    
    # Update activated_at if first activation
    if not lic[3]:  # activated_at is NULL
        expires_at = datetime.now() + timedelta(days=lic[2])
        db.execute(
            text("UPDATE licenses SET activated_at=NOW(), expires_at=:exp WHERE license_key=:key"),
            {"key": license_key, "exp": expires_at}
        )
        db.commit()
        return {
            "status": "activated",
            "tier": lic[1],
            "duration_days": lic[2],
            "expires_at": expires_at.isoformat(),
            "max_devices": max_devices,
            "device_count": device_count + 1,
            "message": "Kích hoạt thành công!"
        }
    
    db.commit()
    return {
        "status": "activated",
        "tier": lic[1],
        "duration_days": lic[2],
        "expires_at": lic[4].isoformat() if lic[4] else None,
        "max_devices": max_devices,
        "device_count": device_count + 1,
        "message": "Thêm thiết bị thành công!"
    }

'''
            # Append to file
            content = content.rstrip() + fix_code
            print("Added /activate-v2 endpoint")
        else:
            print("No /activate endpoint found!")
            return
    
    with open('/app/app.py', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()

