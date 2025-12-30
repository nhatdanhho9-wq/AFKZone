#!/usr/bin/env python3
"""Complete fix - rewrite problematic functions"""

with open('/app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Completely rewrite /admin/users
old_users = '''@app.get("/admin/users")
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

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Get total count
    total = db.execute(text(f"SELECT COUNT(*) FROM devices WHERE {where_sql}"), params).scalar()

    # Get users
    results = db.execute(text(f"""
        SELECT * FROM devices
        WHERE {where_sql}
        ORDER BY last_seen DESC
        LIMIT :limit OFFSET :offset
    """), params).fetchall()

    return {
        "total": total or 0,
        "page": page,
        "limit": limit,
        "users": [
            {
                "device_id": r[1],
                "device_fingerprint": r[2],
                "device_model": r[3],
                "os_version": r[4],
                "app_version": r[5],
                "first_seen": r[6].isoformat() if r[6] else None,
                "last_seen": r[7].isoformat() if r[7] else None,
                "last_ip": r[8],
                "license_key": r[9],
                "license_status": r[10],
                "license_tier": r[11],
                "license_expires_at": r[12],
                "is_active": r[13],
                "total_sessions": r[14]
            } for r in results
        ]
    }'''

new_users = '''@app.get("/admin/users")
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

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Get users from license_devices
    query = f"""
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
    """
    
    results = db.execute(text(query), params).fetchall()
    
    # Get total count
    count_query = f"""
        SELECT COUNT(DISTINCT ld.device_id)
        FROM license_devices ld
        JOIN licenses l ON ld.license_key = l.license_key
        LEFT JOIN devices d ON ld.device_id = d.device_id
        WHERE ld.is_active=TRUE AND ({where_sql})
    """
    total = db.execute(text(count_query), params).scalar()

    return {
        "total": total or 0,
        "page": page,
        "limit": limit,
        "users": [
            {
                "device_id": r[0] if len(r) > 0 else None,
                "device_model": r[1] if len(r) > 1 else None,
                "app_version": r[2] if len(r) > 2 else None,
                "last_seen": r[3].isoformat() if len(r) > 3 and r[3] else None,
                "license_key": r[4] if len(r) > 4 else None,
                "license_tier": r[5] if len(r) > 5 else None,
                "license_expires_at": r[6] if len(r) > 6 else None,
                "is_active": r[7] if len(r) > 7 else None,
                "total_sessions": r[8] if len(r) > 8 else 0
            } for r in results
        ]
    }'''

if old_users in content:
    content = content.replace(old_users, new_users)
    print('✅ Replaced /admin/users function')

# 2. Fix dashboard stats
old_stats = '''    # Active licenses
    active_licenses = db.execute(text(
        "SELECT COUNT(*) FROM licenses WHERE expires_at > EXTRACT(EPOCH FROM NOW()) * 1000 AND activated_at IS NOT NULL"
    )).scalar()

    # Expired licenses
    expired_licenses = db.execute(text(
        "SELECT COUNT(*) FROM licenses WHERE expires_at <= EXTRACT(EPOCH FROM NOW()) * 1000 AND activated_at IS NOT NULL"
    )).scalar()'''

new_stats = '''    # Active licenses (expires_at is timestamp)
    try:
        active_licenses = db.execute(text(
            "SELECT COUNT(*) FROM licenses WHERE expires_at > NOW() AND activated_at IS NOT NULL"
        )).scalar()
    except:
        # Fallback: try bigint comparison
        active_licenses = db.execute(text(
            "SELECT COUNT(*) FROM licenses WHERE expires_at::bigint > (EXTRACT(EPOCH FROM NOW())::bigint * 1000) AND activated_at IS NOT NULL"
        )).scalar()

    # Expired licenses
    try:
        expired_licenses = db.execute(text(
            "SELECT COUNT(*) FROM licenses WHERE expires_at <= NOW() AND activated_at IS NOT NULL"
        )).scalar()
    except:
        # Fallback: try bigint comparison
        expired_licenses = db.execute(text(
            "SELECT COUNT(*) FROM licenses WHERE expires_at::bigint <= (EXTRACT(EPOCH FROM NOW())::bigint * 1000) AND activated_at IS NOT NULL"
        )).scalar()'''

if old_stats in content:
    content = content.replace(old_stats, new_stats)
    print('✅ Fixed dashboard stats')

# 3. Fix /list endpoint
if 'def list_licenses(request: Request = None' in content:
    # Ensure proper header handling
    content = content.replace(
        'def list_licenses(request: Request = None, db: Session = Depends(get_db)):',
        '''def list_licenses(request: Request = None, db: Session = Depends(get_db)):
    """List all licenses - admin_key required in header"""
    from fastapi import Header
    # Get admin_key from header
    admin_key = None
    if request:
        admin_key = request.headers.get("admin_key") or request.headers.get("admin-key")
    if not admin_key or admin_key != "afkzone-admin-2025":'''
    )
    # Remove duplicate check
    content = content.replace(
        '    if not admin_key or admin_key != "afkzone-admin-2025":\n        raise HTTPException(status_code=401, detail="Unauthorized")',
        '        raise HTTPException(status_code=401, detail="Unauthorized")'
    )
    print('✅ Fixed /list endpoint')

with open('/app/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ All fixes applied')

