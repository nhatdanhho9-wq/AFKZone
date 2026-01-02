#!/usr/bin/env python3
"""Add unrevoke endpoint"""

NEW_ENDPOINT = '''

@app.post("/admin/licenses/{license_key}/unrevoke")
async def unrevoke_license(license_key: str, token: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Unrevoke a license - restore access"""
    try:
        result = db.execute(text("""
            UPDATE licenses 
            SET is_revoked = false, revoked_at = NULL, revoked_reason = NULL
            WHERE license_key = :key
        """), {"key": license_key})
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="License not found")
        
        return {"message": "License unrevoked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

'''

def main():
    with open('/app/app.py', 'r') as f:
        content = f.read()
    
    if '/unrevoke' in content:
        print("Unrevoke endpoint already exists")
        return
    
    content = content.rstrip() + NEW_ENDPOINT
    
    with open('/app/app.py', 'w') as f:
        f.write(content)
    
    print("Added unrevoke endpoint!")

if __name__ == "__main__":
    main()

