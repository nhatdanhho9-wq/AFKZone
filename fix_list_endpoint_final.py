#!/usr/bin/env python3
"""Fix /list endpoint to work with header"""

with open('/app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace /list endpoint completely
old_list_pattern = r'@app\.get\("/list"\).*?return \{"total": len\(licenses\), "licenses": licenses\}'

# Actually simpler - just ensure it gets header
if 'def list_licenses(request: Request = None' in content:
    # Check current implementation
    list_start = content.find('@app.get("/list")')
    if list_start > 0:
        # Find the function
        func_start = content.find('def list_licenses', list_start)
        if func_start > 0:
            # Get the function body
            func_end = content.find('\n@app.', func_start)
            if func_end == -1:
                func_end = content.find('\n# ====================', func_start)
            
            func_code = content[func_start:func_end]
            
            # Check if it has proper header handling
            if 'request.headers.get("admin_key")' not in func_code:
                # Replace the function
                new_func = '''def list_licenses(request: Request = None, db: Session = Depends(get_db)):
    """List all licenses - admin_key required in header"""
    # Get admin_key from header
    admin_key = None
    if request:
        admin_key = request.headers.get("admin_key") or request.headers.get("admin-key")
    if not admin_key or admin_key != "afkzone-admin-2025":
        raise HTTPException(status_code=401, detail="Unauthorized")
    results = db.execute(text("SELECT * FROM licenses ORDER BY created_at DESC LIMIT 100")).fetchall()
    licenses = []
    for r in results:
        license_data = {
            "license_key": r[1] if len(r) > 1 else None,
            "tier": r[2] if len(r) > 2 else None,
            "duration_days": r[3] if len(r) > 3 else None,
            "activated_at": r[4].isoformat() if len(r) > 4 and r[4] else None,
            "expires_at": r[5].isoformat() if len(r) > 5 and r[5] else None,
            "device_id": r[6] if len(r) > 6 else None,
            "max_devices": r[7] if len(r) > 7 else None,
            "is_revoked": r[9] if len(r) > 9 else False,
            "is_trial": r[11] if len(r) > 11 else False
        }
        licenses.append(license_data)
    return {"total": len(licenses), "licenses": licenses}'''
                
                content = content[:func_start] + new_func + content[func_end:]
                print('✅ Replaced /list function')
            else:
                print('✅ /list endpoint already has header handling')

with open('/app/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ /list endpoint fixed')

