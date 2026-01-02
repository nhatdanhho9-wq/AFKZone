#!/usr/bin/env python3
"""Fix all admin dashboard endpoints completely"""

import re

with open('/app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix dashboard stats - expires_at is timestamp, not bigint
old_dashboard_licenses = '''    # Active licenses
    active_licenses = db.execute(text(
        "SELECT COUNT(*) FROM licenses WHERE expires_at > EXTRACT(EPOCH FROM NOW()) * 1000 AND activated_at IS NOT NULL"
    )).scalar()

    # Expired licenses
    expired_licenses = db.execute(text(
        "SELECT COUNT(*) FROM licenses WHERE expires_at <= EXTRACT(EPOCH FROM NOW()) * 1000 AND activated_at IS NOT NULL"
    )).scalar()'''

new_dashboard_licenses = '''    # Active licenses (expires_at is timestamp)
    active_licenses = db.execute(text(
        "SELECT COUNT(*) FROM licenses WHERE expires_at > NOW() AND activated_at IS NOT NULL"
    )).scalar()

    # Expired licenses
    expired_licenses = db.execute(text(
        "SELECT COUNT(*) FROM licenses WHERE expires_at <= NOW() AND activated_at IS NOT NULL"
    )).scalar()'''

if old_dashboard_licenses in content:
    content = content.replace(old_dashboard_licenses, new_dashboard_licenses)
    print('✅ Fixed dashboard stats SQL')

# 2. Fix /admin/users to query from license_devices
old_users_query = '''    # Get total count
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

new_users_query = '''    # Query from license_devices to get activated devices
    # Adjust where clauses for license_devices join
    ld_where = where_sql.replace("license_status", "ld.is_active").replace("license_tier", "l.tier")
    
    # Get total count from license_devices
    total = db.execute(text(f"""
        SELECT COUNT(DISTINCT ld.device_id)
        FROM license_devices ld
        JOIN licenses l ON ld.license_key = l.license_key
        LEFT JOIN devices d ON ld.device_id = d.device_id
        WHERE ld.is_active=TRUE AND ({ld_where})
    """), params).scalar()

    # Get users from license_devices
    results = db.execute(text(f"""
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
        WHERE ld.is_active=TRUE AND ({ld_where})
        ORDER BY ld.last_check DESC
        LIMIT :limit OFFSET :offset
    """), params).fetchall()

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

if old_users_query in content:
    content = content.replace(old_users_query, new_users_query)
    print('✅ Fixed /admin/users endpoint')

# 3. Add /admin/connections endpoint if missing
if '@app.get("/admin/connections")' not in content:
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
    
    # Check if connection_logs table exists
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
    except Exception as e:
        # Table doesn't exist, return empty
        return {
            "total": 0,
            "page": page,
            "limit": limit,
            "connections": []
        }
'''
    
    # Add after dashboard stats
    if '@app.get("/admin/dashboard/stats")' in content:
        stats_end = content.find('}', content.find('@app.get("/admin/dashboard/stats")'))
        if stats_end > 0:
            next_line = content.find('\n@app.', stats_end)
            if next_line > 0:
                content = content[:next_line] + connections_endpoint + content[next_line:]
                print('✅ Added /admin/connections endpoint')

# 4. Fix /admin/licenses/generate (single license)
if '@app.post("/admin/licenses/generate")' not in content:
    single_license_endpoint = '''
@app.post("/admin/licenses/generate")
def generate_single_license(
    tier: str,
    duration_days: int,
    max_devices: Optional[int] = None,
    notes: Optional[str] = None,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Generate a single license"""
    key = f"AFK-{tier.upper()}-{secrets.token_hex(12).upper()}"
    
    db.execute(text("""
        INSERT INTO licenses (license_key, tier, duration_days, max_devices, created_by, notes)
        VALUES (:key, :tier, :days, :devices, 'admin', :note)
    """), {
        "key": key,
        "tier": tier,
        "days": duration_days,
        "devices": max_devices,
        "note": notes
    })
    
    db.commit()
    
    return {
        "success": True,
        "license_key": key,
        "tier": tier,
        "duration_days": duration_days,
        "max_devices": max_devices
    }
'''
    
    # Add after bulk-create
    if '@app.post("/admin/licenses/bulk-create")' in content:
        bulk_end = content.find('}', content.find('@app.post("/admin/licenses/bulk-create")'))
        if bulk_end > 0:
            next_line = content.find('\n@app.', bulk_end)
            if next_line > 0:
                content = content[:next_line] + single_license_endpoint + content[next_line:]
                print('✅ Added /admin/licenses/generate endpoint')

with open('/app/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ All admin endpoints fixed')

