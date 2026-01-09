"""
AFKZone vNext - Remote MVP v0.1 Router
Device management, trusted allowlist, share tokens, remote sessions.
"""

from __future__ import annotations

import json
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.auth import (
    TokenClaims,
    create_access_token,
    generate_token_code,
    get_current_user,
    get_optional_user,
    hash_password,
    verify_password,
)
from app.models import (
    DeviceInfo,
    DeviceListResponse,
    DeviceRegisterRequest,
    HeartbeatRequest,
    HeartbeatResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RemoteApproveRequest,
    RemoteApproveResponse,
    RemoteClaimRequest,
    RemoteClaimResponse,
    RemotePendingResponse,
    RemoteRequestCreate,
    RemoteRequestInfo,
    RemoteRequestResponse,
    ShareCreateRequest,
    ShareCreateResponse,
    ShareResolveRequest,
    ShareResolveResponse,
    ShareRevokeRequest,
    TrustedApproveRequest,
    TrustedEntry,
    TrustedListResponse,
    TrustedRequestCreate,
    TrustedRevokeRequest,
)

# Import signaling store for session creation
from app.signaling import session_store

APP_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = APP_ROOT / "afkzone2.db"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_remote_tables():
    """Initialize remote MVP tables if they don't exist."""
    conn = _db()
    cur = conn.cursor()
    
    # Read and execute migrations
    for migration in ("001_remote_mvp.sql", "002_remote_mvp_v02.sql"):
        migration_path = APP_ROOT / "migrations" / migration
        if migration_path.exists():
            try:
                cur.executescript(migration_path.read_text())
            except sqlite3.OperationalError:
                # Ignore errors (e.g., columns already exist)
                pass

    # Best-effort schema upgrades for MVP (SQLite)
    for ddl in (
        "ALTER TABLE remote_request ADD COLUMN claim_token TEXT",
        "ALTER TABLE remote_request ADD COLUMN controller_token TEXT",
        "ALTER TABLE share_token ADD COLUMN created_by_device_id TEXT",
        "ALTER TABLE device ADD COLUMN current_session_id TEXT",
        "ALTER TABLE device ADD COLUMN session_started_at TEXT",
        "ALTER TABLE trusted_allowlist ADD COLUMN controller_device_id TEXT",
    ):
        try:
            cur.execute(ddl)
        except sqlite3.OperationalError:
            # Column already exists (or table missing), ignore.
            pass
    
    conn.commit()
    conn.close()


# Initialize tables on module load
_init_remote_tables()


router = APIRouter(tags=["remote"])


# ==================== AUTH ENDPOINTS ====================

@router.post("/auth/register")
async def auth_register(req: RegisterRequest) -> JSONResponse:
    """Register a new account."""
    conn = _db()
    cur = conn.cursor()
    
    # Check if username exists
    existing = cur.execute(
        "SELECT account_id FROM account WHERE username = ?",
        (req.username,)
    ).fetchone()
    
    if existing:
        conn.close()
        raise HTTPException(status_code=409, detail="Username already exists")
    
    account_id = secrets.token_urlsafe(16)
    password_hash = hash_password(req.password)
    
    cur.execute(
        "INSERT INTO account (account_id, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (account_id, req.username, password_hash, _utc_now_iso())
    )
    conn.commit()
    conn.close()
    
    return JSONResponse({"ok": True, "account_id": account_id})


@router.post("/auth/login", response_model=LoginResponse)
async def auth_login(req: LoginRequest) -> LoginResponse:
    """Login and get access token. Optionally auto-register device."""
    conn = _db()
    cur = conn.cursor()
    
    row = cur.execute(
        "SELECT account_id, password_hash FROM account WHERE username = ?",
        (req.username,)
    ).fetchone()
    
    if not row or not verify_password(req.password, row["password_hash"]):
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    account_id = row["account_id"]
    token, expires_at = create_access_token(account_id, req.username)
    
    device_id = None
    account_switched = False
    
    # Auto-register device if provided
    if req.device_id or req.device_name:
        device_id = req.device_id or secrets.token_urlsafe(18)
        device_name = req.device_name or f"Device-{device_id[:8]}"
        
        # Check if device was previously registered to another account
        existing = cur.execute(
            "SELECT account_id FROM device WHERE device_id = ?",
            (device_id,)
        ).fetchone()
        
        if existing and existing["account_id"] != account_id:
            # Account switch: mark old registration as switched_out
            account_switched = True
            cur.execute(
                """
                INSERT INTO device_session_history (device_id, account_id, action, ts)
                VALUES (?, ?, 'switch_out', ?)
                """,
                (device_id, existing["account_id"], _utc_now_iso())
            )
        
        # Upsert device with new account
        session_id = secrets.token_urlsafe(12)
        cur.execute(
            """
            INSERT INTO device (device_id, account_id, device_name, device_type, last_seen, online, current_session_id, session_started_at, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
            ON CONFLICT(device_id) DO UPDATE SET
                account_id = excluded.account_id,
                device_name = excluded.device_name,
                device_type = excluded.device_type,
                last_seen = excluded.last_seen,
                online = 1,
                current_session_id = excluded.current_session_id,
                session_started_at = excluded.session_started_at
            """,
            (device_id, account_id, device_name, req.device_type, _utc_now_iso(), session_id, _utc_now_iso(), _utc_now_iso())
        )
        
        # Log login event
        cur.execute(
            """
            INSERT INTO device_session_history (device_id, account_id, action, ts)
            VALUES (?, ?, 'login', ?)
            """,
            (device_id, account_id, _utc_now_iso())
        )
    
    # Handle previous_device_id invalidation (explicit account switch)
    if req.previous_device_id and req.previous_device_id != device_id:
        cur.execute(
            """
            UPDATE device SET online = 0, current_session_id = NULL
            WHERE device_id = ? AND account_id != ?
            """,
            (req.previous_device_id, account_id)
        )
        cur.execute(
            """
            INSERT INTO device_session_history (device_id, account_id, action, ts)
            SELECT device_id, account_id, 'switch_out', ?
            FROM device WHERE device_id = ? AND account_id != ?
            """,
            (_utc_now_iso(), req.previous_device_id, account_id)
        )
        account_switched = True
    
    conn.commit()
    conn.close()
    
    return LoginResponse(
        access_token=token,
        account_id=account_id,
        expires_in=86400,
        device_id=device_id,
        account_switched=account_switched,
    )


@router.post("/auth/logout")
async def auth_logout(
    device_id: Optional[str] = None,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Logout: mark device offline and log session end."""
    conn = _db()
    cur = conn.cursor()
    
    if device_id:
        # Mark specific device as offline
        cur.execute(
            """
            UPDATE device SET online = 0, current_session_id = NULL
            WHERE device_id = ? AND account_id = ?
            """,
            (device_id, user.account_id)
        )
        cur.execute(
            """
            INSERT INTO device_session_history (device_id, account_id, action, ts)
            VALUES (?, ?, 'logout', ?)
            """,
            (device_id, user.account_id, _utc_now_iso())
        )
    
    conn.commit()
    conn.close()
    
    return JSONResponse({"ok": True})


# ==================== DEVICE ENDPOINTS ====================

@router.post("/devices/register")
async def device_register(
    req: DeviceRegisterRequest,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Register a device to the authenticated account."""
    device_id = req.device_id or secrets.token_urlsafe(18)
    conn = _db()
    cur = conn.cursor()
    
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
        (device_id, user.account_id, req.device_name, req.device_type, _utc_now_iso(), _utc_now_iso())
    )
    conn.commit()
    conn.close()
    
    return JSONResponse({"ok": True, "device_id": device_id})


@router.get("/devices", response_model=DeviceListResponse)
async def device_list(user: TokenClaims = Depends(get_current_user)) -> DeviceListResponse:
    """List all devices for the authenticated account."""
    conn = _db()
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
        DeviceInfo(
            device_id=r["device_id"],
            device_name=r["device_name"],
            device_type=r["device_type"],
            online=bool(r["online"]),
            last_seen=r["last_seen"],
            unattended_mode=r["unattended_mode"] or "disabled",
        )
        for r in rows
    ]
    
    return DeviceListResponse(devices=devices)


@router.post("/devices/{device_id}/heartbeat", response_model=HeartbeatResponse)
async def device_heartbeat(
    device_id: str,
    user: TokenClaims = Depends(get_current_user)
) -> HeartbeatResponse:
    """Update device presence (heartbeat)."""
    conn = _db()
    cur = conn.cursor()
    
    cur.execute(
        "UPDATE device SET last_seen = ?, online = 1 WHERE device_id = ? AND account_id = ?",
        (_utc_now_iso(), device_id, user.account_id)
    )
    conn.commit()
    conn.close()
    
    return HeartbeatResponse(ok=True, server_time=_utc_now_iso())


# ==================== TRUSTED ALLOWLIST ENDPOINTS ====================

@router.get("/trusted/list", response_model=TrustedListResponse)
async def trusted_list(user: TokenClaims = Depends(get_current_user)) -> TrustedListResponse:
    """List trusted allowlist entries for the account's devices."""
    conn = _db()
    cur = conn.cursor()
    
    rows = cur.execute(
        """
        SELECT t.id, t.target_device_id, t.requester_account_id, t.requester_device_id,
               t.status, t.created_at, t.approved_at
        FROM trusted_allowlist t
        JOIN device d ON t.target_device_id = d.device_id
        WHERE d.account_id = ?
        ORDER BY t.created_at DESC
        """,
        (user.account_id,)
    ).fetchall()
    conn.close()
    
    entries = [
        TrustedEntry(
            id=r["id"],
            target_device_id=r["target_device_id"],
            requester_account_id=r["requester_account_id"],
            requester_device_id=r["requester_device_id"],
            status=r["status"],
            created_at=r["created_at"],
            approved_at=r["approved_at"],
        )
        for r in rows
    ]
    
    return TrustedListResponse(entries=entries)


@router.post("/trusted/request")
async def trusted_request(
    req: TrustedRequestCreate,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Request to be added to trusted allowlist for a device."""
    conn = _db()
    cur = conn.cursor()
    
    # Get device owner
    device = cur.execute(
        "SELECT account_id FROM device WHERE device_id = ?",
        (req.target_device_id,)
    ).fetchone()
    
    if not device:
        conn.close()
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Check if already trusted
    existing = cur.execute(
        """
        SELECT id, status FROM trusted_allowlist
        WHERE target_device_id = ? AND requester_account_id = ? AND status != 'revoked'
        """,
        (req.target_device_id, user.account_id)
    ).fetchone()
    
    if existing:
        conn.close()
        if existing["status"] == "approved":
            return JSONResponse({"ok": True, "status": "already_trusted", "id": existing["id"]})
        elif existing["status"] == "pending":
            return JSONResponse({"ok": True, "status": "pending", "id": existing["id"]})
    
    # Create trust request
    cur.execute(
        """
        INSERT INTO trusted_allowlist
        (owner_account_id, target_device_id, requester_account_id, requester_device_id, status, created_at)
        VALUES (?, ?, ?, ?, 'pending', ?)
        """,
        (device["account_id"], req.target_device_id, user.account_id, req.requester_device_id, _utc_now_iso())
    )
    request_id = cur.lastrowid
    conn.commit()
    conn.close()
    
    return JSONResponse({"ok": True, "status": "pending", "id": request_id})


@router.post("/trusted/approve")
async def trusted_approve(
    req: TrustedApproveRequest,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Approve a trust request (owner only)."""
    conn = _db()
    cur = conn.cursor()
    
    # Verify ownership
    row = cur.execute(
        """
        SELECT t.id, t.status, d.account_id as owner_id
        FROM trusted_allowlist t
        JOIN device d ON t.target_device_id = d.device_id
        WHERE t.id = ?
        """,
        (req.request_id,)
    ).fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Request not found")
    
    if row["owner_id"] != user.account_id:
        conn.close()
        raise HTTPException(status_code=403, detail="Only device owner can approve")
    
    if row["status"] != "pending":
        conn.close()
        raise HTTPException(status_code=409, detail=f"Request already {row['status']}")
    
    # Get requester_device_id from the trust request to save as controller_device_id
    trust_req = cur.execute(
        "SELECT requester_device_id, target_device_id FROM trusted_allowlist WHERE id = ?",
        (req.request_id,)
    ).fetchone()
    
    # Update with optional controller_device_id for device pair auto-approve
    if req.trust and trust_req and trust_req["requester_device_id"]:
        # Save device pair for future auto-approve
        cur.execute(
            """
            UPDATE trusted_allowlist 
            SET status = 'approved', approved_at = ?, updated_at = ?, controller_device_id = ?
            WHERE id = ?
            """,
            (_utc_now_iso(), _utc_now_iso(), trust_req["requester_device_id"], req.request_id)
        )
    else:
        # Standard approval without device pair
        cur.execute(
            "UPDATE trusted_allowlist SET status = 'approved', approved_at = ?, updated_at = ? WHERE id = ?",
            (_utc_now_iso(), _utc_now_iso(), req.request_id)
        )
    
    conn.commit()
    conn.close()
    
    return JSONResponse({"ok": True, "trusted_device_pair": bool(req.trust and trust_req and trust_req["requester_device_id"])})


@router.post("/trusted/revoke")
async def trusted_revoke(
    req: TrustedRevokeRequest,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Revoke trust (owner only)."""
    conn = _db()
    cur = conn.cursor()
    
    # Verify ownership
    row = cur.execute(
        """
        SELECT t.id, d.account_id as owner_id
        FROM trusted_allowlist t
        JOIN device d ON t.target_device_id = d.device_id
        WHERE t.id = ?
        """,
        (req.entry_id,)
    ).fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Entry not found")
    
    if row["owner_id"] != user.account_id:
        conn.close()
        raise HTTPException(status_code=403, detail="Only device owner can revoke")
    
    cur.execute(
        "UPDATE trusted_allowlist SET status = 'revoked', updated_at = ? WHERE id = ?",
        (_utc_now_iso(), req.entry_id)
    )
    conn.commit()
    conn.close()
    
    return JSONResponse({"ok": True})


# ==================== SHARE TOKEN ENDPOINTS ====================

@router.post("/share/create", response_model=ShareCreateResponse)
async def share_create(
    req: ShareCreateRequest,
    user: TokenClaims = Depends(get_current_user)
) -> ShareCreateResponse:
    """Create a share token for a device."""
    conn = _db()
    cur = conn.cursor()
    
    # Verify device ownership
    device = cur.execute(
        "SELECT account_id FROM device WHERE device_id = ?",
        (req.device_id,)
    ).fetchone()
    
    if not device or device["account_id"] != user.account_id:
        conn.close()
        raise HTTPException(status_code=403, detail="Not authorized for this device")
    
    # Generate unique token
    for _ in range(10):  # Retry up to 10 times for uniqueness
        token = generate_token_code(6)
        exists = cur.execute("SELECT 1 FROM share_token WHERE token = ?", (token,)).fetchone()
        if not exists:
            break
    else:
        conn.close()
        raise HTTPException(status_code=500, detail="Could not generate unique token")
    
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=req.expires_hours)).isoformat().replace("+00:00", "Z")
    
    cur.execute(
        """
        INSERT INTO share_token (token, device_id, account_id, expires_at, max_uses, created_at, created_by_device_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (token, req.device_id, user.account_id, expires_at, req.max_uses, _utc_now_iso(), req.created_by_device_id)
    )
    conn.commit()
    conn.close()
    
    return ShareCreateResponse(token=token, expires_at=expires_at)


@router.post("/share/resolve", response_model=ShareResolveResponse)
async def share_resolve(req: ShareResolveRequest) -> ShareResolveResponse:
    """Resolve a share token to get device info."""
    conn = _db()
    cur = conn.cursor()
    
    row = cur.execute(
        """
        SELECT s.device_id, s.account_id, s.expires_at, s.max_uses, s.uses_count, s.revoked,
               d.device_name
        FROM share_token s
        JOIN device d ON s.device_id = d.device_id
        WHERE s.token = ?
        """,
        (req.token.upper(),)
    ).fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Token not found")
    
    if row["revoked"]:
        raise HTTPException(status_code=410, detail="Token has been revoked")
    
    # Check expiry
    expires = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expires:
        raise HTTPException(status_code=410, detail="Token has expired")
    
    if row["uses_count"] >= row["max_uses"]:
        raise HTTPException(status_code=410, detail="Token usage limit reached")
    
    return ShareResolveResponse(
        device_id=row["device_id"],
        device_name=row["device_name"],
        account_id=row["account_id"],
    )


@router.post("/share/revoke")
async def share_revoke(
    req: ShareRevokeRequest,
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Revoke a share token (owner only)."""
    conn = _db()
    cur = conn.cursor()
    
    row = cur.execute(
        "SELECT account_id FROM share_token WHERE token = ?",
        (req.token.upper(),)
    ).fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Token not found")
    
    if row["account_id"] != user.account_id:
        conn.close()
        raise HTTPException(status_code=403, detail="Only token creator can revoke")
    
    cur.execute("UPDATE share_token SET revoked = 1 WHERE token = ?", (req.token.upper(),))
    conn.commit()
    conn.close()
    
    return JSONResponse({"ok": True})


# ==================== REMOTE SESSION ENDPOINTS ====================

@router.post("/remote/request", response_model=RemoteRequestResponse)
async def remote_request(
    req: RemoteRequestCreate,
    request: Request,
    user: Optional[TokenClaims] = Depends(get_optional_user)
) -> RemoteRequestResponse:
    """Request a remote session to a device."""
    conn = _db()
    cur = conn.cursor()
    
    target_device_id = req.target_device_id
    share_token_used = None
    
    # Resolve via share token if provided
    if req.share_token:
        token_row = cur.execute(
            """
            SELECT device_id, expires_at, max_uses, uses_count, revoked
            FROM share_token WHERE token = ?
            """,
            (req.share_token.upper(),)
        ).fetchone()
        
        if not token_row:
            conn.close()
            raise HTTPException(status_code=404, detail="Share token not found")
        
        if token_row["revoked"]:
            conn.close()
            raise HTTPException(status_code=410, detail="Token revoked")
        
        expires = datetime.fromisoformat(token_row["expires_at"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expires:
            conn.close()
            raise HTTPException(status_code=410, detail="Token expired")
        
        if token_row["uses_count"] >= token_row["max_uses"]:
            conn.close()
            raise HTTPException(status_code=410, detail="Token usage limit reached")
        
        target_device_id = token_row["device_id"]
        share_token_used = req.share_token.upper()
        
        # Increment usage
        cur.execute(
            "UPDATE share_token SET uses_count = uses_count + 1 WHERE token = ?",
            (share_token_used,)
        )
    
    if not target_device_id:
        conn.close()
        raise HTTPException(status_code=400, detail="Must provide target_device_id or share_token")
    
    # Check if trusted (auto-approve)
    # Priority 1: Check device pair (controller_device_id → host_device_id)
    # Priority 2: Check account-level trust (requester_account_id → target_device_id)
    auto_approve = False
    if user and req.requester_device_id:
        # Check device pair first (most specific)
        device_pair_trusted = cur.execute(
            """
            SELECT id FROM trusted_allowlist
            WHERE target_device_id = ? 
              AND controller_device_id = ? 
              AND status = 'approved'
            """,
            (target_device_id, req.requester_device_id)
        ).fetchone()
        auto_approve = device_pair_trusted is not None
    
    if not auto_approve and user:
        # Fallback to account-level trust
        account_trusted = cur.execute(
            """
            SELECT id FROM trusted_allowlist
            WHERE target_device_id = ? AND requester_account_id = ? AND status = 'approved'
            """,
            (target_device_id, user.account_id)
        ).fetchone()
        auto_approve = account_trusted is not None
    
    request_id = secrets.token_urlsafe(12)
    claim_token = secrets.token_urlsafe(18)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
    
    status = "approved" if auto_approve else "pending"
    session_id = None
    controller_token = None
    
    if auto_approve:
        # Create signaling session immediately
        session = session_store.create_session(
            target_device_id=target_device_id,
            region="default",
        )
        session_id = session.session_id
        controller_token = session.controller_token
    
    cur.execute(
        """
        INSERT INTO remote_request
        (request_id, target_device_id, requester_account_id, requester_device_id, share_token, status, created_at, expires_at, session_id, claim_token, controller_token)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            request_id,
            target_device_id,
            user.account_id if user else None,
            req.requester_device_id,
            share_token_used,
            status,
            _utc_now_iso(),
            expires_at,
            session_id,
            claim_token,
            controller_token,
        )
    )
    conn.commit()
    conn.close()
    
    return RemoteRequestResponse(
        request_id=request_id,
        status=status,
        session_id=session_id,
        claim_token=claim_token,
    )


@router.get("/remote/pending", response_model=RemotePendingResponse)
async def remote_pending(user: TokenClaims = Depends(get_current_user)) -> RemotePendingResponse:
    """Get pending remote requests for devices owned by the account."""
    conn = _db()
    cur = conn.cursor()
    
    rows = cur.execute(
        """
        SELECT r.request_id,
               r.target_device_id,
               d.device_name AS target_device_name,
               r.requester_account_id,
               r.requester_device_id,
               r.share_token,
               s.created_by_device_id AS share_created_by_device_id,
               r.status,
               r.created_at,
               r.expires_at
        FROM remote_request r
        JOIN device d ON r.target_device_id = d.device_id
        LEFT JOIN share_token s ON r.share_token = s.token
        WHERE d.account_id = ? AND r.status = 'pending'
        ORDER BY r.created_at DESC
        """,
        (user.account_id,)
    ).fetchall()
    conn.close()
    
    requests = [
        RemoteRequestInfo(
            request_id=r["request_id"],
            target_device_id=r["target_device_id"],
            target_device_name=r["target_device_name"],
            requester_account_id=r["requester_account_id"],
            requester_device_id=r["requester_device_id"],
            share_token=r["share_token"],
            share_created_by_device_id=r["share_created_by_device_id"],
            status=r["status"],
            created_at=r["created_at"],
            expires_at=r["expires_at"],
        )
        for r in rows
    ]
    
    return RemotePendingResponse(requests=requests)


@router.post("/remote/approve", response_model=RemoteApproveResponse)
async def remote_approve(
    req: RemoteApproveRequest,
    user: TokenClaims = Depends(get_current_user)
) -> RemoteApproveResponse:
    """Approve a pending remote request (owner only)."""
    conn = _db()
    cur = conn.cursor()
    
    # Verify ownership and get request
    row = cur.execute(
        """
        SELECT r.request_id, r.target_device_id, r.status, d.account_id as owner_id
        FROM remote_request r
        JOIN device d ON r.target_device_id = d.device_id
        WHERE r.request_id = ?
        """,
        (req.request_id,)
    ).fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Request not found")
    
    if row["owner_id"] != user.account_id:
        conn.close()
        raise HTTPException(status_code=403, detail="Only device owner can approve")
    
    if row["status"] != "pending":
        conn.close()
        raise HTTPException(status_code=409, detail=f"Request already {row['status']}")
    
    # Create signaling session
    session = session_store.create_session(
        target_device_id=row["target_device_id"],
        region="default",
    )
    
    cur.execute(
        """
        UPDATE remote_request
        SET status = 'approved', approved_by = ?, approved_at = ?, session_id = ?, controller_token = ?
        WHERE request_id = ?
        """,
        (user.account_id, _utc_now_iso(), session.session_id, session.controller_token, req.request_id)
    )
    conn.commit()
    conn.close()
    
    return RemoteApproveResponse(
        ok=True,
        session_id=session.session_id,
        signaling_ws_url=f"/sessions/{session.session_id}/ws",
        controller_token=session.controller_token,
    )


@router.post("/remote/claim", response_model=RemoteClaimResponse)
async def remote_claim(req: RemoteClaimRequest) -> RemoteClaimResponse:
    """
    Requester claims session details after approval using an opaque claim_token.
    This avoids requiring requester auth for MVP and supports anonymous share-token flow.
    """
    conn = _db()
    cur = conn.cursor()
    row = cur.execute(
        """
        SELECT request_id, status, session_id, controller_token, claim_token
        FROM remote_request
        WHERE request_id = ?
        """,
        (req.request_id,),
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Request not found")
    if (row["claim_token"] or "") != req.claim_token:
        raise HTTPException(status_code=403, detail="Invalid claim token")

    status = row["status"]
    session_id = row["session_id"]
    controller_token = row["controller_token"]
    if status != "approved" or not session_id or not controller_token:
        return RemoteClaimResponse(ok=True, status=status)

    return RemoteClaimResponse(
        ok=True,
        status=status,
        session_id=session_id,
        signaling_ws_url=f"/sessions/{session_id}/ws",
        controller_token=controller_token,
    )


@router.post("/remote/reject")
async def remote_reject(
    req: RemoteApproveRequest,  # Same schema, just request_id
    user: TokenClaims = Depends(get_current_user)
) -> JSONResponse:
    """Reject a pending remote request (owner only)."""
    conn = _db()
    cur = conn.cursor()
    
    # Verify ownership
    row = cur.execute(
        """
        SELECT r.request_id, r.status, d.account_id as owner_id
        FROM remote_request r
        JOIN device d ON r.target_device_id = d.device_id
        WHERE r.request_id = ?
        """,
        (req.request_id,)
    ).fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Request not found")
    
    if row["owner_id"] != user.account_id:
        conn.close()
        raise HTTPException(status_code=403, detail="Only device owner can reject")
    
    cur.execute(
        "UPDATE remote_request SET status = 'rejected' WHERE request_id = ?",
        (req.request_id,)
    )
    conn.commit()
    conn.close()
    
    return JSONResponse({"ok": True})
