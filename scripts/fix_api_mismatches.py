#!/usr/bin/env python3
"""
Fix Critical API Mismatches - Backend
Based on OPUS_REVIEW_FULL.md findings

Adds:
1. POST /license/logout - Remove device from license (clear slot)
2. GET /tiers - Get tier names for display
3. Fix /activate response field names
"""

def fix_backend():
    with open('/app/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open('/app/app.py.bak_api_fix', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # ==================== 1. ADD /license/logout ENDPOINT ====================
    logout_endpoint = '''
# ==================== LICENSE LOGOUT ====================
@app.post("/license/logout")
def logout_license(data: dict, db: Session = Depends(get_db)):
    """Remove device from license - clears slot for other devices"""
    license_key = data.get("license_key")
    device_id = data.get("device_id")
    
    if not license_key or not device_id:
        raise HTTPException(status_code=400, detail="Missing license_key or device_id")
    
    # Check if this device is actually linked to this license
    existing = db.execute(
        text("SELECT id FROM license_devices WHERE license_key=:key AND device_id=:device"),
        {"key": license_key, "device": device_id}
    ).fetchone()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Device not found for this license")
    
    # Delete from license_devices table
    db.execute(
        text("DELETE FROM license_devices WHERE license_key=:key AND device_id=:device"),
        {"key": license_key, "device": device_id}
    )
    db.commit()
    
    # Get remaining device count
    remaining = db.execute(
        text("SELECT COUNT(*) FROM license_devices WHERE license_key=:key"),
        {"key": license_key}
    ).scalar() or 0
    
    print(f"✅ Logout: Removed device {device_id[:20]}... from license {license_key}. Remaining: {remaining}")
    
    return {
        "success": True,
        "message": "Thiết bị đã được xóa khỏi license",
        "remaining_devices": remaining
    }

'''
    
    # Check if already exists
    if '@app.post("/license/logout")' not in content:
        # Add after /check endpoint
        check_marker = '@app.post("/check")'
        if check_marker in content:
            # Find end of check_license function
            idx = content.find(check_marker)
            # Find next @app decorator
            next_app = content.find('@app.', idx + len(check_marker))
            if next_app > 0:
                content = content[:next_app] + logout_endpoint + content[next_app:]
                print("✅ Added /license/logout endpoint")
        else:
            # Fallback: add before # Bank Transfer section
            bank_marker = "# Bank Transfer Configuration"
            if bank_marker in content:
                content = content.replace(bank_marker, logout_endpoint + "\n" + bank_marker)
                print("✅ Added /license/logout endpoint (fallback location)")
    else:
        print("⚠️ /license/logout already exists")
    
    # ==================== 2. ADD /tiers ENDPOINT ====================
    tiers_endpoint = '''
# ==================== TIERS API ====================
@app.get("/tiers")
def get_tiers(db: Session = Depends(get_db)):
    """Get all active tiers for display"""
    try:
        results = db.execute(text("""
            SELECT id, tier_key, name, max_devices, description, is_active, display_order
            FROM tiers 
            WHERE is_active = TRUE 
            ORDER BY display_order, id
        """)).fetchall()
        
        tiers = []
        for r in results:
            tiers.append({
                "id": r[0],
                "tier_key": r[1],
                "name": r[2],
                "max_devices": r[3],
                "description": r[4],
                "is_active": r[5],
                "display_order": r[6]
            })
        
        return {"tiers": tiers}
    except Exception as e:
        print(f"❌ Error getting tiers: {e}")
        # Fallback if tiers table doesn't exist
        return {"tiers": [
            {"tier_key": "basic", "name": "Gói Cơ Bản", "max_devices": 2},
            {"tier_key": "pro", "name": "Gói Cao Thủ", "max_devices": 5},
            {"tier_key": "enterprise", "name": "Gói Doanh Nghiệp", "max_devices": -1}
        ]}

'''
    
    if '@app.get("/tiers")' not in content:
        # Add before /products
        products_marker = '@app.get("/products")'
        if products_marker in content:
            content = content.replace(products_marker, tiers_endpoint + products_marker)
            print("✅ Added /tiers endpoint")
        else:
            # Fallback
            if '# Bank Transfer Configuration' in content:
                content = content.replace('# Bank Transfer Configuration', tiers_endpoint + '\n# Bank Transfer Configuration')
                print("✅ Added /tiers endpoint (fallback)")
    else:
        print("⚠️ /tiers already exists")
    
    # ==================== 3. FIX /activate RESPONSE FIELDS ====================
    # Change device_limit to max_devices in responses
    # This is tricky - we need to ensure consistency
    
    # The /activate endpoint returns max_devices already (line ~97, ~172, etc)
    # But /check returns device_limit - need to fix that
    
    old_check_return = '"device_limit": r[2],'
    new_check_return = '"max_devices": r[2],'
    
    if old_check_return in content:
        content = content.replace(old_check_return, new_check_return)
        print("✅ Fixed /check response: device_limit → max_devices")
    else:
        print("⚠️ device_limit field not found or already fixed")
    
    # ==================== 4. ADD /license/info ENDPOINT ====================
    info_endpoint = '''
# ==================== LICENSE INFO ====================
@app.get("/license/info")
def get_license_info(license_key: str, db: Session = Depends(get_db)):
    """Get license information for display in app settings"""
    lic = db.execute(text("""
        SELECT license_key, tier, duration_days, activated_at, expires_at, max_devices, is_revoked
        FROM licenses WHERE license_key = :key
    """), {"key": license_key}).fetchone()
    
    if not lic:
        raise HTTPException(status_code=404, detail="License not found")
    
    # Get active device count
    device_count = db.execute(
        text("SELECT COUNT(*) FROM license_devices WHERE license_key = :key"),
        {"key": license_key}
    ).scalar() or 0
    
    return {
        "license_key": lic[0],
        "tier": lic[1],
        "duration_days": lic[2],
        "activated_at": lic[3].isoformat() if lic[3] else None,
        "expires_at": lic[4].isoformat() if lic[4] else None,
        "max_devices": lic[5],
        "is_revoked": lic[6],
        "active_devices": device_count
    }

'''
    
    if '@app.get("/license/info")' not in content:
        # Add after /license/logout
        if '@app.post("/license/logout")' in content:
            idx = content.find('@app.post("/license/logout")')
            # Find next @app decorator
            next_app = content.find('@app.', idx + 30)
            if next_app > 0:
                content = content[:next_app] + info_endpoint + content[next_app:]
                print("✅ Added /license/info endpoint")
    else:
        print("⚠️ /license/info already exists")
    
    # Write updated file
    with open('/app/app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ Backend API fixes applied!")
    print("   - /license/logout: Remove device from license")
    print("   - /license/info: Get license details")
    print("   - /tiers: Get tier names")
    print("   - Fixed device_limit → max_devices in /check")

if __name__ == '__main__':
    fix_backend()
