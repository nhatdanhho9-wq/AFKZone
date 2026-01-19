"""
Trusted router - trusted device management endpoints.
"""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.models import TrustRequestCreate, TrustApproveRequest
from app.utils import get_db, utc_now_iso, get_current_user, TokenClaims, api_success, api_error

router = APIRouter()


@router.post("/trusted/request")
async def trusted_request(
    req: TrustRequestCreate,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Request to add a device to trusted list."""
    conn = get_db()
    cur = conn.cursor()
    
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=24)
    
    cur.execute(
        """
        INSERT INTO trusted_allowlist 
        (owner_account_id, target_device_id, requester_account_id, requester_device_id, status, created_at, expires_at)
        VALUES (?, ?, ?, ?, 'pending', ?, ?)
        """,
        (user.account_id, req.target_device_id, user.account_id, req.requester_device_id,
         now.isoformat(), expires_at.isoformat())
    )
    trust_id = cur.lastrowid
    conn.commit()
    conn.close()
    
    print(f"TRUST_REQUEST trust_request_id={trust_id} target_device_id={req.target_device_id} requester_account_id={user.account_id}")
    
    return JSONResponse(status_code=201, content=api_success({
        "trust_request_id": trust_id,
        "status": "pending",
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
    }))


@router.post("/trusted/approve")
async def trusted_approve(
    req: TrustApproveRequest,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Approve a pending trust request."""
    conn = get_db()
    cur = conn.cursor()
    
    row = cur.execute(
        "SELECT * FROM trusted_allowlist WHERE id = ?",
        (req.trust_request_id,)
    ).fetchone()
    
    if not row:
        conn.close()
        return api_error("TRUST_NOT_FOUND", "Trust request not found", 404)
    
    cur.execute(
        """
        UPDATE trusted_allowlist 
        SET status = 'approved', allow_input_control = ?, allow_file_transfer = ?, approved_at = ?
        WHERE id = ?
        """,
        (1 if req.allow_input_control else 0, 1 if req.allow_file_transfer else 0, 
         utc_now_iso(), req.trust_request_id)
    )
    conn.commit()
    conn.close()
    
    print(f"TRUST_APPROVE trust_id={req.trust_request_id} target_device_id={row['target_device_id']} approver_account_id={user.account_id}")
    
    return JSONResponse(api_success({
        "trust_id": req.trust_request_id,
        "status": "approved",
        "permissions": {
            "allow_input_control": req.allow_input_control,
            "allow_file_transfer": req.allow_file_transfer,
        }
    }))


@router.get("/trusted/list")
async def trusted_list(
    device_id: str = None,
    direction: str = None,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Get list of trusted devices for current user."""
    conn = get_db()
    cur = conn.cursor()
    
    query = """
        SELECT t.*, d.device_name
        FROM trusted_allowlist t
        LEFT JOIN device d ON t.target_device_id = d.device_id
        WHERE t.owner_account_id = ? AND t.status = 'approved'
    """
    params = [user.account_id]
    
    if device_id:
        query += " AND t.target_device_id = ?"
        params.append(device_id)
    
    rows = cur.execute(query, params).fetchall()
    conn.close()
    
    trusted_devices = [
        {
            "trust_id": r["id"],
            "device_id": r["target_device_id"],
            "device_name": r["device_name"] or "Unknown Device",
            "direction": "outbound",
            "permissions": {
                "allow_input_control": bool(r["allow_input_control"]),
                "allow_file_transfer": bool(r["allow_file_transfer"]),
            },
            "created_at": r["created_at"],
            "last_used_at": r["approved_at"],
        }
        for r in rows
    ]
    
    return JSONResponse(api_success({"trusted_devices": trusted_devices}))


@router.delete("/trusted/{trust_id}")
async def trusted_revoke(
    trust_id: int,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Remove a device from trusted list."""
    conn = get_db()
    cur = conn.cursor()
    
    row = cur.execute(
        "SELECT * FROM trusted_allowlist WHERE id = ? AND owner_account_id = ?",
        (trust_id, user.account_id)
    ).fetchone()
    
    if not row:
        conn.close()
        return api_error("TRUST_NOT_FOUND", "Trust relationship not found", 404)
    
    cur.execute(
        "UPDATE trusted_allowlist SET status = 'revoked' WHERE id = ?",
        (trust_id,)
    )
    conn.commit()
    conn.close()
    
    print(f"TRUST_REVOKE trust_id={trust_id} revoked_by={user.account_id}")
    
    return JSONResponse(api_success({
        "trust_id": trust_id,
        "status": "revoked",
    }))
