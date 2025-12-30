#!/usr/bin/env python3
"""Fix /check endpoint to block revoked licenses"""

def main():
    with open('/app/app.py', 'r') as f:
        content = f.read()
    
    # Find the /check endpoint and add revoked check
    # Look for the check endpoint response
    
    # Add check for is_revoked in the check endpoint
    old_check = '''if license_data['expires_at'] < datetime.now():
            raise HTTPException(status_code=400, detail="License expired")'''
    
    new_check = '''if license_data['expires_at'] < datetime.now():
            raise HTTPException(status_code=400, detail="License expired")
        
        # Check if license is revoked
        if license_data.get('is_revoked'):
            raise HTTPException(status_code=403, detail="License has been revoked")'''
    
    if old_check in content:
        content = content.replace(old_check, new_check)
        print("Added revoked check to /check endpoint")
    else:
        print("Could not find check endpoint pattern, trying alternative...")
        # Try to find and patch differently
        if "is_revoked" not in content or "License has been revoked" not in content:
            # Add a simple check at the activate endpoint too
            old_activate = '''# Check if license exists'''
            new_activate = '''# Check if license is revoked first
        revoke_check = db.execute(text("SELECT is_revoked FROM licenses WHERE license_key = :key"), {"key": license_key}).fetchone()
        if revoke_check and revoke_check[0]:
            raise HTTPException(status_code=403, detail="License has been revoked by admin")
        
        # Check if license exists'''
            if old_activate in content:
                content = content.replace(old_activate, new_activate)
                print("Added revoked check to /activate endpoint")
    
    with open('/app/app.py', 'w') as f:
        f.write(content)
    
    print("Done!")

if __name__ == "__main__":
    main()

