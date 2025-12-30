# Additional Admin Endpoints for AFK Zone License API
# Add these to app.py.original

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from database import get_db

# ==================== CONNECTION TRACKING ====================

class ConnectionLog(BaseModel):
    id: Optional[int] = None
    device_id: str
    peer_id: str
    connection_type: str  # remote, file_transfer, view_camera, terminal
    ip_address: str
    connected_at: datetime
    disconnected_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    bytes_sent: Optional[int] = None
    bytes_received: Optional[int] = None
    license_key: Optional[str] = None

@app.get("/admin/connections")
def get_connections(
    page: int = 1,
    limit: int = 100,
    device_id: Optional[str] = None,
    license_key: Optional[str] = None,
    connection_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
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

    if start_date:
        where_clauses.append("connected_at >= :start_date")
        params["start_date"] = start_date

    if end_date:
        where_clauses.append("connected_at <= :end_date")
        params["end_date"] = end_date

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Get total count
    total = db.execute(text(f"SELECT COUNT(*) FROM connection_logs WHERE {where_sql}"), params).scalar()

    # Get connections
    results = db.execute(text(f"""
        SELECT 
            cl.id, cl.device_id, cl.peer_id, cl.connection_type, 
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

    connections = []
    for r in results:
        connections.append({
            "id": r[0],
            "device_id": r[1],
            "peer_id": r[2],
            "connection_type": r[3],
            "ip_address": r[4],
            "connected_at": r[5].isoformat() if r[5] else None,
            "disconnected_at": r[6].isoformat() if r[6] else None,
            "duration_seconds": r[7],
            "bytes_sent": r[8],
            "bytes_received": r[9],
            "license_key": r[10],
            "device_model": r[11],
            "app_version": r[12],
            "license_tier": r[13]
        })

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "connections": connections
    }

@app.post("/admin/connections/log")
def log_connection(
    device_id: str,
    peer_id: str,
    connection_type: str,
    ip_address: str,
    license_key: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Log a new connection (called by RustDesk server or client)"""
    db.execute(text("""
        INSERT INTO connection_logs 
        (device_id, peer_id, connection_type, ip_address, connected_at, license_key)
        VALUES (:device_id, :peer_id, :connection_type, :ip_address, NOW(), :license_key)
    """), {
        "device_id": device_id,
        "peer_id": peer_id,
        "connection_type": connection_type,
        "ip_address": ip_address,
        "license_key": license_key
    })
    db.commit()
    return {"success": True}

@app.put("/admin/connections/{connection_id}/disconnect")
def disconnect_connection(
    connection_id: int,
    bytes_sent: Optional[int] = None,
    bytes_received: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Log connection disconnect"""
    # Get connection start time
    conn = db.execute(text(
        "SELECT connected_at FROM connection_logs WHERE id=:id"
    ), {"id": connection_id}).fetchone()

    if not conn:
        raise HTTPException(404, "Connection not found")

    connected_at = conn[0]
    disconnected_at = datetime.now()
    duration = int((disconnected_at - connected_at).total_seconds())

    db.execute(text("""
        UPDATE connection_logs
        SET disconnected_at=:disconnected_at, 
            duration_seconds=:duration,
            bytes_sent=:bytes_sent,
            bytes_received=:bytes_received
        WHERE id=:id
    """), {
        "id": connection_id,
        "disconnected_at": disconnected_at,
        "duration": duration,
        "bytes_sent": bytes_sent,
        "bytes_received": bytes_received
    })
    db.commit()
    return {"success": True}

# ==================== DEVICE MANAGEMENT ====================

@app.delete("/admin/devices/{device_id}")
def remove_device(
    device_id: str,
    license_key: Optional[str] = None,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Remove device from license or delete device completely"""
    
    if license_key:
        # Remove device from specific license
        db.execute(text("""
            UPDATE license_devices 
            SET is_active=FALSE, deactivated_at=NOW()
            WHERE device_id=:device_id AND license_key=:license_key
        """), {"device_id": device_id, "license_key": license_key})
        db.commit()
        return {
            "success": True,
            "message": f"Device {device_id} removed from license {license_key}"
        }
    else:
        # Remove device from all licenses
        db.execute(text("""
            UPDATE license_devices 
            SET is_active=FALSE, deactivated_at=NOW()
            WHERE device_id=:device_id
        """), {"device_id": device_id})
        
        # Optionally delete device record
        db.execute(text("DELETE FROM devices WHERE device_id=:device_id"), {"device_id": device_id})
        db.commit()
        return {
            "success": True,
            "message": f"Device {device_id} removed from all licenses and deleted"
        }

@app.get("/admin/devices/{device_id}")
def get_device_info(
    device_id: str,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Get full device information"""
    device = db.execute(text("""
        SELECT * FROM devices WHERE device_id=:device_id
    """), {"device_id": device_id}).fetchone()

    if not device:
        raise HTTPException(404, "Device not found")

    # Get all licenses for this device
    licenses = db.execute(text("""
        SELECT ld.license_key, ld.activated_at, ld.last_check, ld.is_active,
               l.tier, l.expires_at, l.is_revoked
        FROM license_devices ld
        JOIN licenses l ON ld.license_key = l.license_key
        WHERE ld.device_id=:device_id
        ORDER BY ld.activated_at DESC
    """), {"device_id": device_id}).fetchall()

    # Get connection history
    connections = db.execute(text("""
        SELECT id, peer_id, connection_type, ip_address, connected_at, disconnected_at, duration_seconds
        FROM connection_logs
        WHERE device_id=:device_id
        ORDER BY connected_at DESC
        LIMIT 50
    """), {"device_id": device_id}).fetchall()

    return {
        "device": {
            "device_id": device[0],
            "device_model": device[1],
            "app_version": device[2],
            "last_seen": device[3].isoformat() if device[3] else None,
            "total_sessions": device[4],
            "license_key": device[5],
            "license_status": device[6],
            "license_tier": device[7],
            "license_expires_at": device[8]
        },
        "licenses": [
            {
                "license_key": l[0],
                "activated_at": l[1].isoformat() if l[1] else None,
                "last_check": l[2].isoformat() if l[2] else None,
                "is_active": l[3],
                "tier": l[4],
                "expires_at": l[5],
                "is_revoked": l[6]
            } for l in licenses
        ],
        "recent_connections": [
            {
                "id": c[0],
                "peer_id": c[1],
                "connection_type": c[2],
                "ip_address": c[3],
                "connected_at": c[4].isoformat() if c[4] else None,
                "disconnected_at": c[5].isoformat() if c[5] else None,
                "duration_seconds": c[6]
            } for c in connections
        ]
    }

# ==================== LICENSE GENERATION ====================

class GenerateLicenseRequest(BaseModel):
    tier: str
    duration_days: int
    max_devices: Optional[int] = None
    notes: Optional[str] = None

@app.post("/admin/licenses/generate")
def generate_license(
    req: GenerateLicenseRequest,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Generate a single license key"""
    
    # Use default max_devices if not provided
    max_devices = req.max_devices
    if max_devices is None:
        max_devices = DEVICE_LIMITS.get(req.tier, 2)
    
    # Generate license key
    key = f"AFK-{req.tier.upper()}-{secrets.token_hex(12).upper()}"
    
    # Calculate expiry (will be set on activation)
    expires_timestamp = int((datetime.now() + timedelta(days=req.duration_days)).timestamp() * 1000)
    
    # Insert license
    db.execute(text("""
        INSERT INTO licenses (license_key, tier, duration_days, expires_at, max_devices, created_by, notes)
        VALUES (:key, :tier, :days, :exp, :devices, 'admin', :note)
    """), {
        "key": key,
        "tier": req.tier,
        "days": req.duration_days,
        "exp": expires_timestamp,
        "devices": max_devices,
        "note": req.notes
    })
    
    db.commit()
    
    return {
        "success": True,
        "license_key": key,
        "tier": req.tier,
        "duration_days": req.duration_days,
        "max_devices": max_devices,
        "expires_at": expires_timestamp
    }

# ==================== PRODUCT UPDATE NOTIFICATION ====================

@app.post("/admin/products/{product_id}/notify")
def notify_product_update(
    product_id: int,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Notify all clients to refresh product data"""
    # This endpoint can be used to trigger cache invalidation
    # Clients should call /products with cache-busting after this
    
    product = db.execute(text(
        "SELECT * FROM products WHERE id=:id"
    ), {"id": product_id}).fetchone()
    
    if not product:
        raise HTTPException(404, "Product not found")
    
    return {
        "success": True,
        "message": "Clients will refresh product data on next request",
        "product_id": product_id
    }

