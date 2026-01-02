#!/usr/bin/env python3
"""Add logout endpoint to app.py for removing device from license"""

import subprocess
import sys

# The logout endpoint code to add
logout_endpoint = '''

# Logout device from license
class LogoutRequest(BaseModel):
    license_key: str
    device_id: str

@app.post("/license/logout")
async def logout_device(request: LogoutRequest, db: Session = Depends(get_db)):
    """Remove device from license - called when user logs out from client"""
    try:
        # Find license
        license_result = db.execute(
            text("SELECT id FROM licenses WHERE license_key = :key"),
            {"key": request.license_key}
        ).fetchone()
        
        if not license_result:
            return {"success": False, "message": "License not found"}
        
        license_id = license_result[0]
        
        # Remove device from license_devices
        db.execute(
            text("DELETE FROM license_devices WHERE license_id = :lid AND device_id = :did"),
            {"lid": license_id, "did": request.device_id}
        )
        db.commit()
        
        return {"success": True, "message": "Device logged out successfully"}
    except Exception as e:
        db.rollback()
        print(f"Error logging out device: {e}")
        return {"success": False, "message": str(e)}

# Get license info including device count
@app.get("/license/info")
async def get_license_info(license_key: str, db: Session = Depends(get_db)):
    """Get license info including activated device count"""
    try:
        # Get license details
        license_result = db.execute(
            text("""
                SELECT l.id, l.tier, l.expires_at, l.max_devices
                FROM licenses l
                WHERE l.license_key = :key
            """),
            {"key": license_key}
        ).fetchone()
        
        if not license_result:
            raise HTTPException(status_code=404, detail="License not found")
        
        license_id = license_result[0]
        tier = license_result[1]
        expires_at = license_result[2]
        max_devices = license_result[3] if license_result[3] else -1
        
        # Count activated devices
        device_count_result = db.execute(
            text("SELECT COUNT(*) FROM license_devices WHERE license_id = :lid"),
            {"lid": license_id}
        ).fetchone()
        
        device_count = device_count_result[0] if device_count_result else 0
        
        return {
            "tier": tier,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "max_devices": max_devices,
            "device_count": device_count
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting license info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

'''

def main():
    # Read current app.py
    with open('/app/app.py', 'r') as f:
        content = f.read()
    
    # Check if endpoints already exist
    if '/license/logout' in content:
        print("Logout endpoint already exists")
        return
    
    # Find a good place to insert - after the verify_token function
    insert_marker = '@app.get("/admin")'
    
    if insert_marker in content:
        # Insert before @app.get("/admin")
        content = content.replace(insert_marker, logout_endpoint + '\n' + insert_marker)
    else:
        # Append to end
        content += logout_endpoint
    
    # Write back
    with open('/app/app.py', 'w') as f:
        f.write(content)
    
    print("Successfully added logout and license info endpoints")

if __name__ == "__main__":
    main()

