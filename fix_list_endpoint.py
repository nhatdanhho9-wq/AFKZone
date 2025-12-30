#!/usr/bin/env python3
"""Fix /list endpoint to include max_devices and is_revoked"""

with open('/app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the /list endpoint
import re

# Pattern to find the list endpoint
pattern = r'@app\.get\("/list"\)\s+def list_licenses[^}]+return \{[^}]+\}'

# New endpoint code
new_endpoint = '''@app.get("/list")
def list_licenses(admin_key: str = Header(None), db: Session = Depends(get_db)):
    if admin_key != "afkzone-admin-2025":
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

# Replace using simpler method - find the function and replace
lines = content.split('\n')
new_lines = []
in_list_func = False
skip_until_return = False

for i, line in enumerate(lines):
    if '@app.get("/list")' in line:
        in_list_func = True
        new_lines.append(new_endpoint)
        skip_until_return = True
        continue
    
    if skip_until_return:
        if line.strip().startswith('@') or (line.strip().startswith('def ') and 'list_licenses' not in line):
            skip_until_return = False
            in_list_func = False
            new_lines.append(line)
        # Skip lines until we're out of the function
        continue
    
    new_lines.append(line)

with open('/app/app.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print('✅ Updated /list endpoint')

