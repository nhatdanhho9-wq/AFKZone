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


# ==================== AGENT ENDPOINTS ====================

from pydantic import BaseModel
from typing import Optional


class HeartbeatRequest(BaseModel):
    status: str = "online"  # online | idle | offline
    fps: Optional[int] = None
    bitrate_kbps: Optional[int] = None


class RemoteAccessRequest(BaseModel):
    enabled: Optional[bool] = None
    remote_access_enabled: Optional[bool] = None
    
    def get_enabled(self) -> bool:
        """Get enabled value from either field."""
        if self.enabled is not None:
            return self.enabled
        if self.remote_access_enabled is not None:
            return self.remote_access_enabled
        return True  # Default to enabled


class DeviceRegisterRequest(BaseModel):
    name: str
    type: str = "cloud"
    vcpu: int = 2
    ram_gb: int = 4
    description: Optional[str] = None


class DeviceUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    vcpu: Optional[int] = None
    ram_gb: Optional[int] = None


@router.patch("/devices/{device_id}")
async def update_device(
    device_id: str,
    req: DeviceUpdateRequest,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Update device name/description (rename)."""
    conn = get_db()
    cur = conn.cursor()
    
    # Verify ownership
    row = cur.execute(
        "SELECT * FROM devices WHERE id = ? AND owner_user_id = ?",
        (device_id, user.user_id)
    ).fetchone()
    
    if not row:
        conn.close()
        return api_error("NOT_OWNER", "Device not found or not owned by you", 403)
    
    updates = []
    params = []
    
    if req.name is not None:
        updates.append("name = ?")
        params.append(req.name)
    if req.description is not None:
        updates.append("description = ?")
        params.append(req.description)
    if req.type is not None:
        updates.append("type = ?")
        params.append(req.type)
    if req.vcpu is not None:
        updates.append("vcpu = ?")
        params.append(req.vcpu)
    if req.ram_gb is not None:
        updates.append("ram_gb = ?")
        params.append(req.ram_gb)
    
    if updates:
        params.append(device_id)
        cur.execute(f"UPDATE devices SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    
    # Get updated device
    row = cur.execute("SELECT * FROM devices WHERE id = ?", (device_id,)).fetchone()
    conn.close()
    
    print(f"DEVICE_UPDATE device_id={device_id} user_id={user.user_id}")
    
    return JSONResponse(api_success({
        "device": {
            "id": row["id"],
            "name": row["name"],
            "type": row["type"],
            "status": row["status"],
            "vcpu": row["vcpu"],
            "ram_gb": row["ram_gb"],
            "description": row["description"]
        }
    }))


@router.delete("/devices/{device_id}")
async def delete_device(
    device_id: str,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Delete a device."""
    conn = get_db()
    cur = conn.cursor()
    
    # Verify ownership
    row = cur.execute(
        "SELECT * FROM devices WHERE id = ? AND owner_user_id = ?",
        (device_id, user.user_id)
    ).fetchone()
    
    if not row:
        conn.close()
        return api_error("NOT_OWNER", "Device not found or not owned by you", 403)
    
    # Delete from trusted_devices first
    cur.execute("DELETE FROM trusted_devices WHERE device_id = ?", (device_id,))
    # Delete device
    cur.execute("DELETE FROM devices WHERE id = ?", (device_id,))
    conn.commit()
    conn.close()
    
    print(f"DEVICE_DELETE device_id={device_id} user_id={user.user_id}")
    
    return JSONResponse(api_success({"deleted": True, "device_id": device_id}))


@router.post("/devices/{device_id}/heartbeat")
async def device_heartbeat(
    device_id: str,
    req: HeartbeatRequest = None
) -> JSONResponse:
    """Device agent heartbeat - updates status, stats, and last_seen."""
    conn = get_db()
    cur = conn.cursor()
    
    status = req.status if req else "online"
    fps = req.fps if req else None
    bitrate = req.bitrate_kbps if req else None
    now = utc_now_iso()
    
    # Build dynamic update
    updates = ["status = ?", "last_seen_at = ?"]
    params = [status, now]
    
    if fps is not None:
        updates.append("last_fps = ?")
        params.append(fps)
    if bitrate is not None:
        updates.append("last_bitrate_kbps = ?")
        params.append(bitrate)
    
    params.append(device_id)
    cur.execute(f"UPDATE devices SET {', '.join(updates)} WHERE id = ?", params)
    affected = cur.rowcount
    conn.commit()
    conn.close()
    
    if affected == 0:
        return api_error("DEVICE_NOT_FOUND", "Device not found", 404)
    
    log_msg = f"HEARTBEAT device_id={device_id} status={status}"
    if fps:
        log_msg += f" fps={fps}"
    if bitrate:
        log_msg += f" bitrate_kbps={bitrate}"
    print(log_msg)
    
    return JSONResponse(api_success({"status": status, "server_time": now}))


@router.patch("/devices/{device_id}/remote-access")
async def toggle_remote_access(
    device_id: str,
    req: RemoteAccessRequest,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Toggle remote access permission for device."""
    conn = get_db()
    cur = conn.cursor()
    
    # Verify ownership
    row = cur.execute(
        "SELECT * FROM devices WHERE id = ? AND owner_user_id = ?",
        (device_id, user.user_id)
    ).fetchone()
    
    if not row:
        conn.close()
        return api_error("NOT_OWNER", "Device not found or not owned by you", 403)
    
    # Update remote_access_enabled field
    enabled_value = req.get_enabled()
    cur.execute(
        "UPDATE devices SET remote_access_enabled = ? WHERE id = ?",
        (1 if enabled_value else 0, device_id)
    )
    conn.commit()
    conn.close()
    
    action = "ENABLE_SCREEN_CAPTURE_SENT" if enabled_value else "DISABLE_SCREEN_CAPTURE"
    print(f"{action} device_id={device_id} user_id={user.user_id}")
    
    return JSONResponse(api_success({
        "device_id": device_id,
        "remote_access_enabled": enabled_value
    }))


@router.get("/devices/{device_id}/remote-access")
async def get_remote_access(
    device_id: str,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Get remote access permission state."""
    conn = get_db()
    cur = conn.cursor()
    
    row = cur.execute(
        "SELECT remote_access_enabled FROM devices WHERE id = ? AND owner_user_id = ?",
        (device_id, user.user_id)
    ).fetchone()
    conn.close()
    
    if not row:
        return api_error("NOT_OWNER", "Device not found or not owned by you", 403)
    
    return JSONResponse(api_success({
        "device_id": device_id,
        "remote_access_enabled": bool(row["remote_access_enabled"]) if row["remote_access_enabled"] is not None else True
    }))


@router.post("/devices/register")
async def register_device(
    req: DeviceRegisterRequest,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Register a new device (from agent)."""
    import secrets
    
    conn = get_db()
    cur = conn.cursor()
    
    device_id = f"dev_{secrets.token_urlsafe(8)}"
    agent_token = secrets.token_urlsafe(32)  # Agent-scoped token
    now = utc_now_iso()
    
    cur.execute(
        """INSERT INTO devices 
           (id, owner_user_id, name, type, status, vcpu, ram_gb, description, remote_access_enabled, agent_token_hash, last_seen_at, created_at) 
           VALUES (?, ?, ?, ?, 'online', ?, ?, ?, 1, ?, ?, ?)""",
        (device_id, user.user_id, req.name, req.type, req.vcpu, req.ram_gb, req.description, agent_token, now, now)
    )
    conn.commit()
    conn.close()
    
    print(f"DEVICE_REGISTER device_id={device_id} owner={user.user_id} name={req.name}")
    
    return JSONResponse(status_code=201, content=api_success({
        "device": {
            "id": device_id,
            "name": req.name,
            "type": req.type,
            "status": "online"
        },
        "agent_token": agent_token
    }))
