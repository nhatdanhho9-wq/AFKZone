# Admin endpoints to append to app.py

@app.get("/admin/connections")
def get_connections(
    page: int = 1,
    limit: int = 100,
    device_id: Optional[str] = None,
    license_key: Optional[str] = None,
    connection_type: Optional[str] = None,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Get all connection logs with full info"""
    offset = (page - 1) * limit
    where_clauses = []
    params = {"limit": limit, "offset": offset}

    if device_id:
        where_clauses.append("device_id=:device_id")
        params["device_id"] = device_id
    if license_key:
        where_clauses.append("license_key=:license_key")
        params["license_key"] = license_key
    if connection_type:
        where_clauses.append("connection_type=:connection_type")
        params["connection_type"] = connection_type

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    try:
        total = db.execute(text(f"SELECT COUNT(*) FROM connection_logs WHERE {where_sql}"), params).scalar()
        results = db.execute(text(f"""
            SELECT cl.id, cl.device_id, cl.peer_id, cl.connection_type, 
                   cl.ip_address, cl.connected_at, cl.disconnected_at,
                   cl.duration_seconds, cl.bytes_sent, cl.bytes_received,
                   cl.license_key, d.device_model, d.app_version, l.tier
            FROM connection_logs cl
            LEFT JOIN devices d ON cl.device_id = d.device_id
            LEFT JOIN licenses l ON cl.license_key = l.license_key
            WHERE {where_sql}
            ORDER BY cl.connected_at DESC
            LIMIT :limit OFFSET :offset
        """), params).fetchall()
    except:
        return {"total": 0, "page": page, "limit": limit, "connections": []}

    connections = []
    for r in results:
        connections.append({
            "id": r[0], "device_id": r[1], "peer_id": r[2], "connection_type": r[3],
            "ip_address": r[4], "connected_at": r[5].isoformat() if r[5] else None,
            "disconnected_at": r[6].isoformat() if r[6] else None,
            "duration_seconds": r[7], "bytes_sent": r[8], "bytes_received": r[9],
            "license_key": r[10], "device_model": r[11], "app_version": r[12], "license_tier": r[13]
        })

    return {"total": total, "page": page, "limit": limit, "connections": connections}

@app.post("/admin/connections/log")
def log_connection(
    device_id: str, peer_id: str, connection_type: str, ip_address: str,
    license_key: Optional[str] = None, db: Session = Depends(get_db)
):
    """Log a new connection"""
    try:
        db.execute(text("""
            INSERT INTO connection_logs (device_id, peer_id, connection_type, ip_address, connected_at, license_key)
            VALUES (:device_id, :peer_id, :connection_type, :ip_address, NOW(), :license_key)
        """), {"device_id": device_id, "peer_id": peer_id, "connection_type": connection_type,
               "ip_address": ip_address, "license_key": license_key})
        db.commit()
        return {"success": True}
    except:
        return {"success": False}

@app.delete("/admin/devices/{device_id}")
def remove_device(
    device_id: str, license_key: Optional[str] = None,
    token: dict = Depends(verify_token), db: Session = Depends(get_db)
):
    """Admin: Remove device"""
    if license_key:
        db.execute(text("UPDATE license_devices SET is_active=FALSE, deactivated_at=NOW() WHERE device_id=:device_id AND license_key=:license_key"),
                  {"device_id": device_id, "license_key": license_key})
    else:
        db.execute(text("UPDATE license_devices SET is_active=FALSE, deactivated_at=NOW() WHERE device_id=:device_id"), {"device_id": device_id})
        db.execute(text("DELETE FROM devices WHERE device_id=:device_id"), {"device_id": device_id})
    db.commit()
    return {"success": True, "message": f"Device {device_id} removed"}

@app.get("/admin/devices/{device_id}")
def get_device_info(device_id: str, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Get device info"""
    device = db.execute(text("SELECT * FROM devices WHERE device_id=:device_id"), {"device_id": device_id}).fetchone()
    if not device:
        raise HTTPException(404, "Device not found")
    
    licenses = db.execute(text("""
        SELECT ld.license_key, ld.activated_at, ld.last_check, ld.is_active, l.tier, l.expires_at, l.is_revoked
        FROM license_devices ld JOIN licenses l ON ld.license_key = l.license_key
        WHERE ld.device_id=:device_id ORDER BY ld.activated_at DESC
    """), {"device_id": device_id}).fetchall()
    
    try:
        connections = db.execute(text("""
            SELECT id, peer_id, connection_type, ip_address, connected_at, disconnected_at, duration_seconds
            FROM connection_logs WHERE device_id=:device_id ORDER BY connected_at DESC LIMIT 50
        """), {"device_id": device_id}).fetchall()
    except:
        connections = []
    
    return {
        "device": {"device_id": device[0], "device_model": device[1] if len(device) > 1 else None,
                  "app_version": device[2] if len(device) > 2 else None, "last_seen": device[3].isoformat() if len(device) > 3 and device[3] else None},
        "licenses": [{"license_key": l[0], "activated_at": l[1].isoformat() if l[1] else None, "tier": l[4]} for l in licenses],
        "recent_connections": [{"id": c[0], "peer_id": c[1], "connection_type": c[2]} for c in connections]
    }

@app.post("/admin/licenses/generate")
def generate_license(
    tier: str, duration_days: int, max_devices: Optional[int] = None, notes: Optional[str] = None,
    token: dict = Depends(verify_token), db: Session = Depends(get_db)
):
    """Admin: Generate license"""
    if max_devices is None:
        max_devices = DEVICE_LIMITS.get(tier, 2)
    key = f"AFK-{tier.upper()}-{secrets.token_hex(12).upper()}"
    expires_timestamp = int((datetime.now() + timedelta(days=duration_days)).timestamp() * 1000)
    
    db.execute(text("""
        INSERT INTO licenses (license_key, tier, duration_days, expires_at, max_devices, created_by, notes)
        VALUES (:key, :tier, :days, :exp, :devices, 'admin', :note)
    """), {"key": key, "tier": tier, "days": duration_days, "exp": expires_timestamp,
           "devices": max_devices, "note": notes})
    db.commit()
    
    return {"success": True, "license_key": key, "tier": tier, "duration_days": duration_days, "max_devices": max_devices}

