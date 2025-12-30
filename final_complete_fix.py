#!/usr/bin/env python3
"""Final complete fix for all admin endpoints"""

with open('/app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix /admin/users - remove duplicate WHERE clauses
# Find and replace the entire get_users function
old_get_users_start = '@app.get("/admin/users")'
old_get_users_end = '    }'

# Actually, let's use a simpler approach - just fix the SQL
if 'WHERE ld.is_active=TRUE\n        WHERE ld.is_active=TRUE' in content:
    content = content.replace(
        'WHERE ld.is_active=TRUE\n        WHERE ld.is_active=TRUE',
        'WHERE ld.is_active=TRUE'
    )
    print('✅ Fixed duplicate WHERE clause')

# Remove any duplicate WHERE/ORDER BY/LIMIT
content = re.sub(r'WHERE.*?\n\s+WHERE', 'WHERE', content, flags=re.DOTALL)
content = re.sub(r'ORDER BY.*?\n\s+ORDER BY', 'ORDER BY', content, flags=re.DOTALL)
content = re.sub(r'LIMIT.*?\n\s+LIMIT', 'LIMIT', content, flags=re.DOTALL)

# 2. Fix /list endpoint - make it work with header
if 'def list_licenses(request: Request = None' in content:
    # Ensure it gets admin_key from header
    lines = content.split('\n')
    new_lines = []
    in_list_func = False
    
    for i, line in enumerate(lines):
        if 'def list_licenses(request: Request = None' in line:
            in_list_func = True
            new_lines.append(line)
            # Add proper header extraction
            new_lines.append('    """List all licenses - admin_key required in header"""')
            new_lines.append('    from fastapi import Request, Header')
            new_lines.append('    # Get admin_key from header')
            new_lines.append('    admin_key = None')
            new_lines.append('    if request:')
            new_lines.append('        admin_key = request.headers.get("admin_key") or request.headers.get("admin-key")')
            new_lines.append('    if not admin_key or admin_key != "afkzone-admin-2025":')
            continue
        
        if in_list_func and 'if not admin_key or admin_key != "afkzone-admin-2025":' in line and 'def list_licenses' in '\n'.join(new_lines[-10:]):
            # Skip duplicate check
            continue
        
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    print('✅ Fixed /list endpoint')

# 3. Fix /admin/licenses/generate - ensure it's POST with JSON body
if 'class SingleLicenseRequest' not in content:
    # Add the class
    if '@app.post("/admin/licenses/generate")' in content:
        pos = content.find('@app.post("/admin/licenses/generate")')
        class_def = '''class SingleLicenseRequest(BaseModel):
    tier: str
    duration_days: int
    max_devices: Optional[int] = None
    notes: Optional[str] = None

'''
        content = content[:pos] + class_def + content[pos:]
        print('✅ Added SingleLicenseRequest class')

# Fix function signature
if 'def generate_single_license(' in content and 'tier: str,' in content:
    # Replace with req parameter
    content = re.sub(
        r'def generate_single_license\(\s*tier: str,\s*duration_days: int,\s*max_devices: Optional\[int\] = None,\s*notes: Optional\[str\] = None,',
        'def generate_single_license(\n    req: SingleLicenseRequest,',
        content
    )
    # Fix references
    content = content.replace('f"AFK-{tier.upper()}-', 'f"AFK-{req.tier.upper()}-')
    content = content.replace('"tier": tier,', '"tier": req.tier,')
    content = content.replace('"days": duration_days,', '"days": req.duration_days,')
    content = content.replace('"devices": max_devices,', '"devices": req.max_devices,')
    content = content.replace('"note": notes', '"note": req.notes')
    print('✅ Fixed generate_single_license function')

# 4. Fix dashboard stats - ensure expires_at comparison works
# Check actual data type first
import subprocess
result = subprocess.run(['docker', 'exec', 'afkzone-license-api', 'python3', '-c', '''
from database import get_db
from sqlalchemy import text
db = next(get_db())
sample = db.execute(text("SELECT expires_at FROM licenses WHERE expires_at IS NOT NULL LIMIT 1")).fetchone()
if sample:
    print(f"TYPE:{type(sample[0]).__name__}")
    print(f"VALUE:{sample[0]}")
else:
    print("NO_DATA")
'''], capture_output=True, text=True)

if 'TYPE:datetime' in result.stdout or 'TYPE:Timestamp' in result.stdout:
    # It's timestamp, use NOW()
    content = content.replace('expires_at > EXTRACT(EPOCH FROM NOW()) * 1000', 'expires_at > NOW()')
    content = content.replace('expires_at <= EXTRACT(EPOCH FROM NOW()) * 1000', 'expires_at <= NOW()')
    print('✅ Fixed dashboard stats for timestamp type')
elif 'TYPE:int' in result.stdout or 'TYPE:float' in result.stdout:
    # It's bigint (milliseconds)
    content = content.replace('expires_at > NOW()', 'expires_at > (EXTRACT(EPOCH FROM NOW())::bigint * 1000)')
    content = content.replace('expires_at <= NOW()', 'expires_at <= (EXTRACT(EPOCH FROM NOW())::bigint * 1000)')
    print('✅ Fixed dashboard stats for bigint type')

# 5. Fix /admin/users - completely rewrite the query
old_users_func = '''@app.get("/admin/users")
def get_users(
    page: int = 1,
    limit: int = 50,
    status: Optional[str] = None,
    tier: Optional[str] = None,
    search: Optional[str] = None,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Get all users with pagination"""
    offset = (page - 1) * limit
    where_clauses = []
    params = {"limit": limit, "offset": offset}

    if status:
        where_clauses.append("license_status=:status")
        params["status"] = status

    if tier:
        where_clauses.append("license_tier=:tier")
        params["tier"] = tier

    if search:
        where_clauses.append("(device_id ILIKE :search OR device_model ILIKE :search)")
        params["search"] = f"%{search}%"

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"'''

new_users_func = '''@app.get("/admin/users")
def get_users(
    page: int = 1,
    limit: int = 50,
    status: Optional[str] = None,
    tier: Optional[str] = None,
    search: Optional[str] = None,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Get all users with pagination - from license_devices"""
    offset = (page - 1) * limit
    where_clauses = []
    params = {"limit": limit, "offset": offset}

    if tier:
        where_clauses.append("l.tier=:tier")
        params["tier"] = tier

    if search:
        where_clauses.append("(ld.device_id ILIKE :search OR d.device_model ILIKE :search)")
        params["search"] = f"%{search}%"

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"'''

if old_users_func in content:
    content = content.replace(old_users_func, new_users_func)
    
    # Also fix the query part
    if 'SELECT DISTINCT' in content and 'FROM license_devices ld' in content:
        # Find and replace the query
        old_query_pattern = r'SELECT DISTINCT.*?LIMIT :limit OFFSET :offset'
        new_query = '''        results = db.execute(text("""
            SELECT DISTINCT 
                ld.device_id,
                COALESCE(d.device_model, 'N/A') as device_model,
                COALESCE(d.app_version, 'N/A') as app_version,
                ld.last_check as last_seen,
                ld.license_key,
                l.tier as license_tier,
                l.expires_at as license_expires_at,
                ld.is_active,
                COALESCE(d.total_sessions, 0) as total_sessions
            FROM license_devices ld
            JOIN licenses l ON ld.license_key = l.license_key
            LEFT JOIN devices d ON ld.device_id = d.device_id
            WHERE ld.is_active=TRUE AND ({where_sql})
            ORDER BY ld.last_check DESC
            LIMIT :limit OFFSET :offset
        """).format(where_sql=where_sql), params).fetchall()
        
        total = db.execute(text("""
            SELECT COUNT(DISTINCT ld.device_id)
            FROM license_devices ld
            JOIN licenses l ON ld.license_key = l.license_key
            LEFT JOIN devices d ON ld.device_id = d.device_id
            WHERE ld.is_active=TRUE AND ({where_sql})
        """).format(where_sql=where_sql), params).scalar()'''
        
        # Use simpler replacement
        content = re.sub(
            r'results = db\.execute\(text\(f?""".*?LIMIT :limit OFFSET :offset.*?"""\), params\)\.fetchall\(\)',
            new_query.split('results =')[1].split('total =')[0].strip(),
            content,
            flags=re.DOTALL
        )
    
    print('✅ Fixed /admin/users function')

with open('/app/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ All fixes applied')

