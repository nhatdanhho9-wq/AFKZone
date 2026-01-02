#!/usr/bin/env python3
"""Add delete license endpoint and fix revoke to block client"""

NEW_ENDPOINTS = '''

# ==================== LICENSE MANAGEMENT ====================

@app.delete("/admin/licenses/{license_key}")
async def delete_license(license_key: str, token: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Permanently delete a license"""
    try:
        # First delete from license_devices
        db.execute(text("DELETE FROM license_devices WHERE license_key = :key"), {"key": license_key})
        # Then delete the license
        result = db.execute(text("DELETE FROM licenses WHERE license_key = :key"), {"key": license_key})
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="License not found")
        
        return {"message": "License deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/licenses/{license_key}/revoke")
async def revoke_license_v2(license_key: str, token: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Revoke a license - will block client on next check"""
    try:
        result = db.execute(text("""
            UPDATE licenses 
            SET is_revoked = true, revoked_at = NOW(), revoked_reason = 'Admin revoked'
            WHERE license_key = :key
        """), {"key": license_key})
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="License not found")
        
        return {"message": "License revoked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

'''

def main():
    with open('/app/app.py', 'r') as f:
        content = f.read()
    
    if '@app.delete("/admin/licenses/{license_key}")' in content:
        print("Delete license endpoint already exists")
        return
    
    content = content.rstrip() + NEW_ENDPOINTS
    
    with open('/app/app.py', 'w') as f:
        f.write(content)
    
    print("Added license management endpoints!")

if __name__ == "__main__":
    main()

