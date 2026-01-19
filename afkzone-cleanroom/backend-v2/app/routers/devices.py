"""
Devices router - device listing and control endpoints.
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.database import get_db
from app.utils import get_current_user, TokenClaims, api_success, api_error, utc_now_iso

router = APIRouter()


@router.get("/devices")
async def list_devices(
    include_trusted: bool = Query(False),
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Get list of user's devices."""
    conn = get_db()
    cur = conn.cursor()
    
    # Get user's own devices
    rows = cur.execute(
        """SELECT d.*, 
           (SELECT 1 FROM trusted_devices t WHERE t.device_id = d.id AND t.user_id = ?) as is_trusted
           FROM devices d WHERE d.owner_user_id = ?
           ORDER BY d.last_seen_at DESC""",
        (user.user_id, user.user_id)
    ).fetchall()
    
    devices = []
    for r in rows:
        devices.append({
            "id": r["id"],
            "name": r["name"],
            "type": r["type"] or "cloud",
            "status": r["status"] or "offline",
            "vcpu": r["vcpu"] or 2,
            "ram_gb": r["ram_gb"] or 4,
            "description": r["description"],
            "is_trusted": bool(r["is_trusted"]),
            "last_seen_at": r["last_seen_at"]
        })
    
    # Include trusted devices from others if requested
    if include_trusted:
        trusted_rows = cur.execute(
            """SELECT d.*, 1 as is_trusted
               FROM devices d
               JOIN trusted_devices t ON d.id = t.device_id
               WHERE t.user_id = ? AND d.owner_user_id != ?""",
            (user.user_id, user.user_id)
        ).fetchall()
        
        for r in trusted_rows:
            devices.append({
                "id": r["id"],
                "name": r["name"],
                "type": r["type"] or "cloud",
                "status": r["status"] or "offline",
                "vcpu": r["vcpu"] or 2,
                "ram_gb": r["ram_gb"] or 4,
                "description": r["description"],
                "is_trusted": True,
                "last_seen_at": r["last_seen_at"]
            })
    
    conn.close()
    
    return JSONResponse(api_success({"devices": devices}))


@router.post("/devices/{device_id}/reboot")
async def reboot_device(
    device_id: str,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Send reboot command to device."""
    conn = get_db()
    cur = conn.cursor()
    
    row = cur.execute(
        "SELECT * FROM devices WHERE id = ? AND owner_user_id = ?",
        (device_id, user.user_id)
    ).fetchone()
    
    if not row:
        conn.close()
        return api_error("NOT_OWNER", "Device not found or not owned by you", 403)
    
    if row["status"] == "offline":
        conn.close()
        return api_error("DEVICE_OFFLINE", "Device is offline", 503)
    
    conn.close()
    
    print(f"DEVICE_REBOOT device_id={device_id} user_id={user.user_id}")
    
    return JSONResponse(api_success())


@router.post("/devices/{device_id}/stop")
async def stop_device(
    device_id: str,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Send stop command to device."""
    conn = get_db()
    cur = conn.cursor()
    
    row = cur.execute(
        "SELECT * FROM devices WHERE id = ? AND owner_user_id = ?",
        (device_id, user.user_id)
    ).fetchone()
    
    if not row:
        conn.close()
        return api_error("NOT_OWNER", "Device not found or not owned by you", 403)
    
    conn.close()
    
    print(f"DEVICE_STOP device_id={device_id} user_id={user.user_id}")
    
    return JSONResponse(api_success())
