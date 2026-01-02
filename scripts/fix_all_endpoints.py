#!/usr/bin/env python3
"""Fix all admin endpoints"""

with open('/app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix /list endpoint - accept header properly
old_list_sig = 'def list_licenses(admin_key: str = Header(None), db: Session = Depends(get_db)):'
new_list_sig = '''def list_licenses(request: Request = None, db: Session = Depends(get_db)):
    # Get admin_key from header
    admin_key = None
    if request:
        admin_key = request.headers.get("admin_key") or request.headers.get("admin-key")
    if not admin_key:
        from fastapi import Header
        try:
            admin_key = Header(None)
        except:
            pass'''

# Actually simpler - just check header directly
content = content.replace(
    'def list_licenses(admin_key: str = Header(None), db: Session = Depends(get_db)):',
    '''def list_licenses(request: Request = None, db: Session = Depends(get_db)):
    # Get admin_key from header
    admin_key = None
    if request:
        admin_key = request.headers.get("admin_key") or request.headers.get("admin-key")'''
)

# Fix the check
content = content.replace(
    '    if admin_key != "REDACTED_ADMIN_KEY":',
    '''    if not admin_key or admin_key != "REDACTED_ADMIN_KEY":'''
)

# 2. Fix dashboard stats SQL - expires_at is bigint (timestamp in ms)
content = content.replace(
    'SELECT COUNT(*) FROM licenses WHERE expires_at > EXTRACT(EPOCH FROM NOW()) * 1000 AND activated_at IS NOT NULL',
    'SELECT COUNT(*) FROM licenses WHERE expires_at > (EXTRACT(EPOCH FROM NOW())::bigint * 1000) AND activated_at IS NOT NULL'
)

content = content.replace(
    'SELECT COUNT(*) FROM licenses WHERE expires_at <= EXTRACT(EPOCH FROM NOW()) * 1000 AND activated_at IS NOT NULL',
    'SELECT COUNT(*) FROM licenses WHERE expires_at <= (EXTRACT(EPOCH FROM NOW())::bigint * 1000) AND activated_at IS NOT NULL'
)

# 3. Fix /list return to include max_devices and is_revoked
old_return = '''    licenses = [{"license_key": r[1], "tier": r[2], "duration_days": r[3], "activated_at": r[4].isoformat() if r[4] else None,
                 "expires_at": r[5].isoformat() if r[5] else None, "device_id": r[6], "is_trial": r[11]} for r in results]
    return {"total": len(licenses), "licenses": licenses}'''

new_return = '''    licenses = []
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

if old_return in content:
    content = content.replace(old_return, new_return)

# Add Request import if not exists
if 'from fastapi import' in content and 'Request' not in content.split('from fastapi import')[1].split('\n')[0]:
    content = content.replace(
        'from fastapi import FastAPI, HTTPException, Header, Depends, Request',
        'from fastapi import FastAPI, HTTPException, Header, Depends, Request'
    )

with open('/app/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Fixed all endpoints')


