"""
Remote router - remote access request/approve endpoints.
"""
import secrets
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.models import RemoteRequest, RemoteApproveRequest, PasswordVerifyRequest
from app.utils import get_db, utc_now_iso, get_current_user, TokenClaims, api_success, api_error, verify_password

router = APIRouter()


@router.post("/remote/request")
async def remote_request(req: RemoteRequest) -> JSONResponse:
    """Request remote access to a target device."""
    conn = get_db()
    cur = conn.cursor()
    
    request_id = secrets.token_urlsafe(12)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=5)
    
    cur.execute(
        """
        INSERT INTO remote_request 
        (request_id, target_device_id, requester_device_id, status, created_at, expires_at)
        VALUES (?, ?, ?, 'pending', ?, ?)
        """,
        (request_id, req.target_device_id, req.requester_device_id, 
         now.isoformat(), expires_at.isoformat())
    )
    conn.commit()
    conn.close()
    
    print(f"REMOTE_REQUEST request_id={request_id} target_device_id={req.target_device_id}")
    
    return JSONResponse(status_code=201, content=api_success({
        "request_id": request_id,
        "status": "pending",
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
    }))


@router.get("/remote/pending")
async def remote_pending(
    device_id: str = None,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Get list of pending remote requests for current user's devices."""
    conn = get_db()
    cur = conn.cursor()
    
    # Get user's devices
    if device_id:
        devices = cur.execute(
            "SELECT device_id FROM device WHERE device_id = ? AND account_id = ?",
            (device_id, user.account_id)
        ).fetchall()
    else:
        devices = cur.execute(
            "SELECT device_id FROM device WHERE account_id = ?",
            (user.account_id,)
        ).fetchall()
    
    device_ids = [d["device_id"] for d in devices]
    
    if not device_ids:
        conn.close()
        return JSONResponse(api_success({"requests": []}))
    
    # Get pending requests
    placeholders = ",".join(["?"] * len(device_ids))
    rows = cur.execute(
        f"""
        SELECT * FROM remote_request 
        WHERE target_device_id IN ({placeholders}) AND status = 'pending'
        ORDER BY created_at DESC
        """,
        device_ids
    ).fetchall()
    conn.close()
    
    requests = [
        {
            "request_id": r["request_id"],
            "requester_device_id": r["requester_device_id"],
            "target_device_id": r["target_device_id"],
            "status": r["status"],
            "created_at": r["created_at"],
            "expires_at": r["expires_at"],
        }
        for r in rows
    ]
    
    return JSONResponse(api_success({"requests": requests}))


@router.post("/remote/approve")
async def remote_approve(
    req: RemoteApproveRequest,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Approve a pending remote request."""
    conn = get_db()
    cur = conn.cursor()
    
    # Get request
    row = cur.execute(
        "SELECT * FROM remote_request WHERE request_id = ?",
        (req.request_id,)
    ).fetchone()
    
    if not row:
        conn.close()
        return api_error("REQUEST_NOT_FOUND", "Request not found", 404)
    
    if row["status"] != "pending":
        conn.close()
        return api_error("REQUEST_EXPIRED", "Request is no longer pending", 410)
    
    # Create session
    session_id = secrets.token_urlsafe(16)
    controller_token = secrets.token_urlsafe(24)
    
    cur.execute(
        "UPDATE remote_request SET status = 'approved', session_id = ? WHERE request_id = ?",
        (session_id, req.request_id)
    )
    conn.commit()
    conn.close()
    
    print(f"APPROVE_ROUTING request_id={req.request_id} target_device_id={row['target_device_id']} session_id={session_id}")
    
    return JSONResponse(api_success({
        "request_id": req.request_id,
        "status": "wait_host_ready",
        "session_id": session_id,
        "signaling_ws_url": f"wss://api.afkzone.io/sessions/{session_id}/ws",
        "controller_token": controller_token,
    }))


@router.post("/remote/deny")
async def remote_deny(
    req: RemoteApproveRequest,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Deny a pending remote request."""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute(
        "UPDATE remote_request SET status = 'denied' WHERE request_id = ?",
        (req.request_id,)
    )
    conn.commit()
    conn.close()
    
    print(f"REMOTE_DENIED request_id={req.request_id}")
    
    return JSONResponse(api_success({
        "request_id": req.request_id,
        "status": "denied",
    }))


@router.post("/remote/host-ready/{request_id}")
async def remote_host_ready(request_id: str) -> JSONResponse:
    """Signal that host device has started screen capture."""
    conn = get_db()
    cur = conn.cursor()
    
    row = cur.execute(
        "SELECT * FROM remote_request WHERE request_id = ?",
        (request_id,)
    ).fetchone()
    conn.close()
    
    if not row:
        return api_error("REQUEST_NOT_FOUND", "Request not found", 404)
    
    session_id = row["session_id"] or secrets.token_urlsafe(16)
    host_token = secrets.token_urlsafe(24)
    
    print(f"HOST_READY_ROUTING request_id={request_id} session_id={session_id}")
    
    return JSONResponse(api_success({
        "session_id": session_id,
        "host_token": host_token,
        "signaling_ws_url": f"wss://api.afkzone.io/sessions/{session_id}/ws",
        "turn_credentials_url": f"/sessions/{session_id}/turn-credentials",
    }))


@router.post("/remote/password/verify")
async def password_verify(req: PasswordVerifyRequest) -> JSONResponse:
    """Verify password for remote access."""
    conn = get_db()
    cur = conn.cursor()
    
    row = cur.execute(
        "SELECT * FROM device WHERE device_id = ?",
        (req.target_device_id,)
    ).fetchone()
    conn.close()
    
    if not row:
        print(f"PASSWORD_VERIFY target_device_id={req.target_device_id} success=false reason=not_found ip=unknown")
        return api_error("DEVICE_NOT_FOUND", "Device not found", 404)
    
    if not row["remote_password_hash"]:
        print(f"PASSWORD_VERIFY target_device_id={req.target_device_id} success=false reason=disabled ip=unknown")
        return api_error("PASSWORD_DISABLED", "Password access not enabled for this device", 403)
    
    if not verify_password(req.password, row["remote_password_hash"]):
        print(f"PASSWORD_VERIFY target_device_id={req.target_device_id} success=false reason=wrong_password ip=unknown")
        return api_error("INVALID_PASSWORD", "Password incorrect", 401)
    
    # Create session
    session_id = secrets.token_urlsafe(16)
    controller_token = secrets.token_urlsafe(24)
    
    print(f"PASSWORD_VERIFY target_device_id={req.target_device_id} success=true session_id={session_id} ip=unknown")
    
    return JSONResponse(api_success({
        "verified": True,
        "session_id": session_id,
        "signaling_ws_url": f"wss://api.afkzone.io/sessions/{session_id}/ws",
        "controller_token": controller_token,
    }))
