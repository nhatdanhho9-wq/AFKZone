"""
Devices router - device management endpoints.
"""
import secrets
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.models import DeviceRegisterRequest
from app.utils import get_db, utc_now_iso, get_current_user, TokenClaims, api_success, api_error

router = APIRouter()


@router.post("/devices/register")
async def device_register(
    req: DeviceRegisterRequest,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Register a device to the authenticated account."""
    device_id = req.device_id or secrets.token_urlsafe(18)
    conn = get_db()
    cur = conn.cursor()
    now = utc_now_iso()
    
    # Upsert device
    cur.execute(
        """
        INSERT INTO device (device_id, account_id, device_name, device_type, last_seen, online, created_at)
        VALUES (?, ?, ?, ?, ?, 1, ?)
        ON CONFLICT(device_id) DO UPDATE SET
            device_name = excluded.device_name,
            device_type = excluded.device_type,
            last_seen = excluded.last_seen,
            online = 1
        """,
        (device_id, user.account_id, req.device_name, req.device_type, now, now)
    )
    conn.commit()
    conn.close()
    
    return JSONResponse(api_success({"device_id": device_id}))


@router.get("/devices")
async def device_list(user: TokenClaims = Depends(get_current_user)) -> JSONResponse:
    """List all devices for the authenticated account."""
    conn = get_db()
    cur = conn.cursor()
    
    rows = cur.execute(
        """
        SELECT device_id, device_name, device_type, online, last_seen, unattended_mode
        FROM device WHERE account_id = ?
        ORDER BY last_seen DESC
        """,
        (user.account_id,)
    ).fetchall()
    conn.close()
    
    devices = [
        {
            "id": r["device_id"],
            "deviceId": r["device_id"],
            "name": r["device_name"],
            "type": r["device_type"],
            "status": "online" if r["online"] else "offline",
            "lastSeen": r["last_seen"],
            "cpu": "Unknown",
            "ram": "Unknown",
            "os": r["device_type"],
        }
        for r in rows
    ]
    
    return JSONResponse(api_success({"devices": devices}))


@router.post("/devices/{device_id}/heartbeat")
async def device_heartbeat(
    device_id: str,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Update device presence (heartbeat)."""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute(
        "UPDATE device SET last_seen = ?, online = 1 WHERE device_id = ? AND account_id = ?",
        (utc_now_iso(), device_id, user.account_id)
    )
    conn.commit()
    conn.close()
    
    return JSONResponse(api_success({"server_time": utc_now_iso()}))


@router.post("/devices/{device_id}/reboot")
async def device_reboot(
    device_id: str,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Send reboot command to device."""
    conn = get_db()
    cur = conn.cursor()
    
    row = cur.execute(
        "SELECT device_id, online FROM device WHERE device_id = ? AND account_id = ?",
        (device_id, user.account_id)
    ).fetchone()
    conn.close()
    
    if not row:
        return api_error("DEVICE_NOT_FOUND", "Device not found", 404)
    
    if not row["online"]:
        return api_error("DEVICE_OFFLINE", "Device is offline", 503)
    
    print(f"DEVICE_COMMAND device_id={device_id} command=reboot user={user.account_id}")
    
    return JSONResponse(api_success({
        "device_id": device_id,
        "status": "rebooting",
        "timestamp": utc_now_iso(),
    }))


@router.post("/devices/{device_id}/stop")
async def device_stop(
    device_id: str,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Send stop command to device."""
    conn = get_db()
    cur = conn.cursor()
    
    row = cur.execute(
        "SELECT device_id, online FROM device WHERE device_id = ? AND account_id = ?",
        (device_id, user.account_id)
    ).fetchone()
    conn.close()
    
    if not row:
        return api_error("DEVICE_NOT_FOUND", "Device not found", 404)
    
    print(f"DEVICE_COMMAND device_id={device_id} command=stop user={user.account_id}")
    
    return JSONResponse(api_success({
        "device_id": device_id,
        "status": "stopping",
        "timestamp": utc_now_iso(),
    }))


@router.get("/devices/{device_id}/status")
async def device_status(
    device_id: str,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Get device status and specs."""
    conn = get_db()
    cur = conn.cursor()
    
    row = cur.execute(
        "SELECT * FROM device WHERE device_id = ? AND account_id = ?",
        (device_id, user.account_id)
    ).fetchone()
    conn.close()
    
    if not row:
        return api_error("DEVICE_NOT_FOUND", "Device not found", 404)
    
    return JSONResponse(api_success({
        "device_id": row["device_id"],
        "name": row["device_name"],
        "type": row["device_type"],
        "status": "online" if row["online"] else "offline",
        "last_seen": row["last_seen"],
        "unattended_mode": row["unattended_mode"] or "disabled",
    }))
