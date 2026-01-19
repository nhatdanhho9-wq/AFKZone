"""
Trusted router - trusted device management.
"""
import secrets
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.database import get_db
from app.schemas import TrustedAddRequest
from app.utils import get_current_user, TokenClaims, api_success, api_error, utc_now_iso

router = APIRouter()


@router.get("/devices")
async def list_trusted(user: TokenClaims = Depends(get_current_user)) -> JSONResponse:
    """Get list of trusted devices."""
    conn = get_db()
    cur = conn.cursor()
    
    rows = cur.execute(
        """SELECT d.* FROM devices d
           JOIN trusted_devices t ON d.id = t.device_id
           WHERE t.user_id = ?""",
        (user.user_id,)
    ).fetchall()
    conn.close()
    
    devices = [
        {
            "id": r["id"],
            "name": r["name"],
            "type": r["type"] or "cloud",
            "status": r["status"] or "offline",
            "vcpu": r["vcpu"] or 2,
            "ram_gb": r["ram_gb"] or 4,
            "description": r["description"],
            "is_trusted": True,
            "last_seen_at": r["last_seen_at"]
        }
        for r in rows
    ]
    
    return JSONResponse(api_success({"devices": devices}))


@router.post("/add")
async def add_trusted(
    req: TrustedAddRequest,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Add device to trusted list."""
    conn = get_db()
    cur = conn.cursor()
    
    # Check device exists
    device = cur.execute("SELECT id FROM devices WHERE id = ?", (req.device_id,)).fetchone()
    if not device:
        conn.close()
        return api_error("DEVICE_NOT_FOUND", "Device not found", 404)
    
    # Check not already trusted
    existing = cur.execute(
        "SELECT id FROM trusted_devices WHERE user_id = ? AND device_id = ?",
        (user.user_id, req.device_id)
    ).fetchone()
    
    if existing:
        conn.close()
        return JSONResponse(api_success())  # Already trusted, return success
    
    cur.execute(
        "INSERT INTO trusted_devices (id, user_id, device_id, created_at) VALUES (?, ?, ?, ?)",
        (secrets.token_urlsafe(8), user.user_id, req.device_id, utc_now_iso())
    )
    conn.commit()
    conn.close()
    
    print(f"TRUST_REQUEST user_id={user.user_id} device_id={req.device_id}")
    
    return JSONResponse(api_success())


@router.post("/revoke")
async def revoke_trusted(
    req: TrustedAddRequest,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Remove device from trusted list."""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute(
        "DELETE FROM trusted_devices WHERE user_id = ? AND device_id = ?",
        (user.user_id, req.device_id)
    )
    conn.commit()
    conn.close()
    
    print(f"TRUST_REVOKE user_id={user.user_id} device_id={req.device_id}")
    
    return JSONResponse(api_success())
