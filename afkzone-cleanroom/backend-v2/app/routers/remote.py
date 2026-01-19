"""
Remote router - remote session management.
"""
import secrets
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.database import get_db
from app.schemas import RemoteRequestBody, PasswordVerifyRequest
from app.utils import (
    get_current_user, TokenClaims, api_success, api_error, 
    utc_now_iso, mint_turn_credentials, verify_password
)

router = APIRouter()


@router.post("/request")
async def request_remote(
    req: RemoteRequestBody,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Request remote access to a device."""
    conn = get_db()
    cur = conn.cursor()
    
    # Check device exists
    device = cur.execute(
        "SELECT * FROM devices WHERE id = ?", (req.device_id,)
    ).fetchone()
    
    if not device:
        conn.close()
        return api_error("DEVICE_NOT_FOUND", "Device not found", 404)
    
    if device["status"] == "offline":
        conn.close()
        return api_error("DEVICE_OFFLINE", "Device is offline", 503)
    
    # Check if trusted or password required
    is_trusted = cur.execute(
        "SELECT 1 FROM trusted_devices WHERE user_id = ? AND device_id = ?",
        (user.user_id, req.device_id)
    ).fetchone()
    
    is_owner = device["owner_user_id"] == user.user_id
    
    if not is_trusted and not is_owner:
        # Need password or trust
        if device["remote_password_hash"]:
            if not req.password:
                conn.close()
                return api_error("PASSWORD_REQUIRED", "Password required for this device", 403)
            if not verify_password(req.password, device["remote_password_hash"]):
                conn.close()
                print(f"PASSWORD_VERIFY device_id={req.device_id} success=false")
                return api_error("INVALID_PASSWORD", "Password incorrect", 401)
            print(f"PASSWORD_VERIFY device_id={req.device_id} success=true")
        else:
            conn.close()
            return api_error("TRUST_REQUIRED", "Device requires trust or password", 403)
    
    # Create session
    session_id = secrets.token_urlsafe(16)
    now = utc_now_iso()
    
    cur.execute(
        "INSERT INTO sessions (id, host_device_id, client_user_id, state, created_at) VALUES (?, ?, ?, 'requested', ?)",
        (session_id, req.device_id, user.user_id, now)
    )
    conn.commit()
    conn.close()
    
    print(f"APPROVE_ROUTING session_id={session_id} device_id={req.device_id} user_id={user.user_id}")
    
    return JSONResponse(api_success({
        "session": {
            "id": session_id,
            "state": "requested",
            "host_device_id": req.device_id,
            "client_user_id": user.user_id,
            "created_at": now
        }
    }))


@router.get("/session/{session_id}")
async def get_session(
    session_id: str,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Get session details with signaling URL and TURN credentials."""
    conn = get_db()
    cur = conn.cursor()
    
    row = cur.execute(
        "SELECT * FROM sessions WHERE id = ? AND client_user_id = ?",
        (session_id, user.user_id)
    ).fetchone()
    conn.close()
    
    if not row:
        return api_error("SESSION_NOT_FOUND", "Session not found", 404)
    
    turn_creds = mint_turn_credentials(session_id)
    
    return JSONResponse(api_success({
        "session": {
            "id": row["id"],
            "state": row["state"],
            "signaling_url": f"wss://api.afkzone.io/sessions/{session_id}/ws",
            "turn_credentials": turn_creds
        }
    }))


@router.post("/password/verify")
async def verify_device_password(
    req: PasswordVerifyRequest,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Verify device password without starting session."""
    conn = get_db()
    cur = conn.cursor()
    
    device = cur.execute(
        "SELECT remote_password_hash FROM devices WHERE id = ?", (req.device_id,)
    ).fetchone()
    conn.close()
    
    if not device:
        return api_error("DEVICE_NOT_FOUND", "Device not found", 404)
    
    if not device["remote_password_hash"]:
        return api_error("PASSWORD_DISABLED", "Device has no password set", 400)
    
    if not verify_password(req.password, device["remote_password_hash"]):
        print(f"PASSWORD_VERIFY device_id={req.device_id} success=false")
        return api_error("INVALID_PASSWORD", "Password incorrect", 401)
    
    print(f"PASSWORD_VERIFY device_id={req.device_id} success=true")
    
    return JSONResponse(api_success())
