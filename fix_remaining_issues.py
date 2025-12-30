#!/usr/bin/env python3
"""Fix remaining admin endpoint issues"""

import re

with open('/app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix /list endpoint to accept header properly
old_list = '''@app.get("/list")
def list_licenses(request: Request = None, db: Session = Depends(get_db)):
    # Get admin_key from header
    admin_key = None
    if request:
        admin_key = request.headers.get("admin_key") or request.headers.get("admin-key")
    if not admin_key or admin_key != "afkzone-admin-2025":'''

new_list = '''@app.get("/list")
def list_licenses(request: Request = None, db: Session = Depends(get_db)):
    # Get admin_key from header or query param
    admin_key = None
    if request:
        admin_key = request.headers.get("admin_key") or request.headers.get("admin-key")
        if not admin_key:
            # Try query param
            from fastapi import Query
            try:
                admin_key = request.query_params.get("admin_key")
            except:
                pass
    if not admin_key or admin_key != "afkzone-admin-2025":'''

if 'def list_licenses(request: Request = None' in content:
    content = content.replace(old_list, new_list)
    print('✅ Fixed /list endpoint header handling')

# 2. Fix /admin/licenses/generate to accept JSON body
old_generate = '''@app.post("/admin/licenses/generate")
def generate_single_license(
    tier: str,
    duration_days: int,
    max_devices: Optional[int] = None,
    notes: Optional[str] = None,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):'''

new_generate = '''class SingleLicenseRequest(BaseModel):
    tier: str
    duration_days: int
    max_devices: Optional[int] = None
    notes: Optional[str] = None

@app.post("/admin/licenses/generate")
def generate_single_license(
    req: SingleLicenseRequest,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):'''

if 'def generate_single_license(' in content and 'tier: str,' in content:
    # Replace function signature
    content = re.sub(
        r'@app\.post\("/admin/licenses/generate"\)\s+def generate_single_license\([^)]+\):',
        new_generate.split('\n@app.post')[1],
        content
    )
    # Add class before function
    if 'class SingleLicenseRequest' not in content:
        generate_pos = content.find('@app.post("/admin/licenses/generate")')
        if generate_pos > 0:
            content = content[:generate_pos] + 'class SingleLicenseRequest(BaseModel):\n    tier: str\n    duration_days: int\n    max_devices: Optional[int] = None\n    notes: Optional[str] = None\n\n' + content[generate_pos:]
    
    # Fix function body to use req
    content = content.replace('key = f"AFK-{tier.upper()}-', 'key = f"AFK-{req.tier.upper()}-')
    content = content.replace('"tier": tier,', '"tier": req.tier,')
    content = content.replace('"days": duration_days,', '"days": req.duration_days,')
    content = content.replace('"devices": max_devices,', '"devices": req.max_devices,')
    content = content.replace('"note": notes', '"note": req.notes')
    content = content.replace('"tier": tier,', '"tier": req.tier,')
    content = content.replace('"duration_days": duration_days,', '"duration_days": req.duration_days,')
    content = content.replace('"max_devices": max_devices', '"max_devices": req.max_devices')
    print('✅ Fixed /admin/licenses/generate endpoint')

# 3. Fix dashboard stats - handle expires_at properly
# Check if expires_at is timestamp or bigint
content = content.replace(
    'expires_at > EXTRACT(EPOCH FROM NOW()) * 1000',
    'expires_at > NOW()'
)
content = content.replace(
    'expires_at <= EXTRACT(EPOCH FROM NOW()) * 1000',
    'expires_at <= NOW()'
)
print('✅ Fixed dashboard stats SQL')

# 4. Fix /admin/users - simplify query
if 'SELECT * FROM devices' in content and 'def get_users' in content:
    # Find the function
    lines = content.split('\n')
    new_lines = []
    in_get_users = False
    skip_until_return = False
    
    for i, line in enumerate(lines):
        if 'def get_users' in line:
            in_get_users = True
        
        if in_get_users and 'SELECT * FROM devices' in line:
            # Replace with simpler query from license_devices
            new_lines.append('        # Query from license_devices')
            new_lines.append('        results = db.execute(text(""')
            new_lines.append('            SELECT DISTINCT')
            new_lines.append('                ld.device_id,')
            new_lines.append('                COALESCE(d.device_model, \'N/A\') as device_model,')
            new_lines.append('                COALESCE(d.app_version, \'N/A\') as app_version,')
            new_lines.append('                ld.last_check as last_seen,')
            new_lines.append('                ld.license_key,')
            new_lines.append('                l.tier as license_tier,')
            new_lines.append('                l.expires_at as license_expires_at,')
            new_lines.append('                ld.is_active,')
            new_lines.append('                COALESCE(d.total_sessions, 0) as total_sessions')
            new_lines.append('            FROM license_devices ld')
            new_lines.append('            JOIN licenses l ON ld.license_key = l.license_key')
            new_lines.append('            LEFT JOIN devices d ON ld.device_id = d.device_id')
            new_lines.append('            WHERE ld.is_active=TRUE')
            new_lines.append('            ORDER BY ld.last_check DESC')
            new_lines.append('            LIMIT :limit OFFSET :offset')
            new_lines.append('        """), params).fetchall()')
            new_lines.append('')
            new_lines.append('        # Get total count')
            new_lines.append('        total = db.execute(text(""')
            new_lines.append('            SELECT COUNT(DISTINCT ld.device_id)')
            new_lines.append('            FROM license_devices ld')
            new_lines.append('            JOIN licenses l ON ld.license_key = l.license_key')
            new_lines.append('            WHERE ld.is_active=TRUE')
            new_lines.append('        """), params).scalar()')
            
            # Skip old query lines
            j = i + 1
            while j < len(lines) and ('SELECT' in lines[j] or 'FROM devices' in lines[j] or 'WHERE' in lines[j] or 'ORDER BY' in lines[j] or 'LIMIT' in lines[j]):
                j += 1
            i = j - 1
            continue
        
        if in_get_users and '"device_id": r[1]' in line:
            # Replace mapping
            new_lines.append('                "device_id": r[0] if len(r) > 0 else None,')
            new_lines.append('                "device_model": r[1] if len(r) > 1 else None,')
            new_lines.append('                "app_version": r[2] if len(r) > 2 else None,')
            new_lines.append('                "last_seen": r[3].isoformat() if len(r) > 3 and r[3] else None,')
            new_lines.append('                "license_key": r[4] if len(r) > 4 else None,')
            new_lines.append('                "license_tier": r[5] if len(r) > 5 else None,')
            new_lines.append('                "license_expires_at": r[6] if len(r) > 6 else None,')
            new_lines.append('                "is_active": r[7] if len(r) > 7 else None,')
            new_lines.append('                "total_sessions": r[8] if len(r) > 8 else 0')
            # Skip old mapping
            j = i + 1
            while j < len(lines) and ('r[' in lines[j] or '}' in lines[j] or '"device' in lines[j] or '"license' in lines[j] or '"total' in lines[j]):
                j += 1
            i = j - 1
            continue
        
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    print('✅ Fixed /admin/users endpoint')

with open('/app/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ All fixes applied')

