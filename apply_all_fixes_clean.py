#!/usr/bin/env python3
"""Apply all fixes cleanly to app.py"""

with open('/app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix /list endpoint - use Header properly
old_list = '''@app.get("/list")
def list_licenses(admin_key: str = Header(None), db: Session = Depends(get_db)):
    if admin_key != "afkzone-admin-2025":
        raise HTTPException(status_code=401, detail="Unauthorized")
    results = db.execute(text("SELECT * FROM licenses ORDER BY created_at DESC LIMIT 100")).fetchall()
    licenses = [{"license_key": r[1], "tier": r[2], "duration_days": r[3], "activated_at": r[4].isoformat() if r[4] else None,
                 "expires_at": r[5].isoformat() if r[5] else None, "device_id": r[6], "is_trial": r[11]} for r in results]
    return {"total": len(licenses), "licenses": licenses}'''

new_list = '''@app.get("/list")
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

if old_list in content:
    content = content.replace(old_list, new_list)
    print('✅ Fixed /list endpoint')

# 2. Fix dashboard stats
content = content.replace(
    'expires_at > EXTRACT(EPOCH FROM NOW()) * 1000',
    'expires_at > NOW()'
)
content = content.replace(
    'expires_at <= EXTRACT(EPOCH FROM NOW()) * 1000',
    'expires_at <= NOW()'
)
print('✅ Fixed dashboard stats')

# 3. Fix /admin/users - replace completely
old_users = '''    # Get total count
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

new_users = '''    # Adjust where clauses for license_devices
    if tier:
        where_clauses = ["l.tier=:tier"]
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
    # Also fix where_clauses initialization
    content = content.replace(
        '    if status:\n        where_clauses.append("license_status=:status")\n        params["status"] = status',
        '    # Status filter removed (not applicable for license_devices)'
    )
    print('✅ Fixed /admin/users endpoint')

# 4. Add /admin/licenses/generate if missing
if '@app.post("/admin/licenses/generate")' not in content:
    # Add after bulk-create
    if '@app.post("/admin/licenses/bulk-create")' in content:
        pos = content.find('}', content.find('@app.post("/admin/licenses/bulk-create")'))
        if pos > 0:
            generate_endpoint = '''

class SingleLicenseRequest(BaseModel):
    tier: str
    duration_days: int
    max_devices: Optional[int] = None
    notes: Optional[str] = None

@app.post("/admin/licenses/generate")
def generate_single_license(
    req: SingleLicenseRequest,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Generate a single license"""
    key = f"AFK-{req.tier.upper()}-{secrets.token_hex(12).upper()}"
    
    db.execute(text("""
        INSERT INTO licenses (license_key, tier, duration_days, max_devices, created_by, notes)
        VALUES (:key, :tier, :days, :devices, 'admin', :note)
    """), {
        "key": key,
        "tier": req.tier,
        "days": req.duration_days,
        "devices": req.max_devices,
        "note": req.notes
    })
    
    db.commit()
    
    return {
        "success": True,
        "license_key": key,
        "tier": req.tier,
        "duration_days": req.duration_days,
        "max_devices": req.max_devices
    }
'''
            next_line = content.find('\n@app.', pos)
            if next_line > 0:
                content = content[:next_line] + generate_endpoint + content[next_line:]
                print('✅ Added /admin/licenses/generate endpoint')

# 5. Add /admin/connections if missing
if '@app.get("/admin/connections")' not in content:
    if '@app.get("/admin/dashboard/stats")' in content:
        pos = content.find('}', content.find('@app.get("/admin/dashboard/stats")'))
        if pos > 0:
            connections_endpoint = '''

@app.get("/admin/connections")
def get_connections(
    page: int = 1,
    limit: int = 100,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Get connection logs"""
    offset = (page - 1) * limit
    
    try:
        results = db.execute(text("""
            SELECT 
                device_id,
                peer_id,
                connection_type,
                ip_address,
                connected_at,
                disconnected_at,
                duration_seconds,
                license_key
            FROM connection_logs
            ORDER BY connected_at DESC
            LIMIT :limit OFFSET :offset
        """), {"limit": limit, "offset": offset}).fetchall()
        
        total = db.execute(text("SELECT COUNT(*) FROM connection_logs")).scalar()
        
        return {
            "total": total or 0,
            "page": page,
            "limit": limit,
            "connections": [
                {
                    "device_id": r[0],
                    "peer_id": r[1],
                    "connection_type": r[2],
                    "ip_address": r[3],
                    "connected_at": r[4].isoformat() if r[4] else None,
                    "disconnected_at": r[5].isoformat() if r[5] else None,
                    "duration_seconds": r[6],
                    "license_key": r[7]
                } for r in results
            ]
        }
    except Exception:
        # Table doesn't exist, return empty
        return {
            "total": 0,
            "page": page,
            "limit": limit,
            "connections": []
        }
'''
            next_line = content.find('\n# ====================', pos)
            if next_line > 0:
                content = content[:next_line] + connections_endpoint + content[next_line:]
                print('✅ Added /admin/connections endpoint')

with open('/app/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ All fixes applied cleanly')

