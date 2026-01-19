"""
Auth router - register, login, refresh endpoints.
"""
import secrets
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.database import get_db
from app.schemas import RegisterRequest, LoginRequest, RefreshRequest
from app.utils import (
    utc_now_iso, hash_password, verify_password, 
    create_access_token, create_refresh_token, api_success, api_error
)

router = APIRouter()


@router.post("/register")
async def register(req: RegisterRequest) -> JSONResponse:
    """Register a new user account."""
    conn = get_db()
    cur = conn.cursor()
    
    # Check email exists
    if cur.execute("SELECT id FROM users WHERE email = ?", (req.email,)).fetchone():
        conn.close()
        return api_error("EMAIL_EXISTS", "Email already registered", 409)
    
    # Check username exists
    if cur.execute("SELECT id FROM users WHERE username = ?", (req.username,)).fetchone():
        conn.close()
        return api_error("USERNAME_EXISTS", "Username already taken", 409)
    
    # Validate password strength
    if len(req.password) < 6:
        conn.close()
        return api_error("WEAK_PASSWORD", "Password must be at least 6 characters", 400)
    
    user_id = secrets.token_urlsafe(16)
    password_hash = hash_password(req.password)
    now = utc_now_iso()
    
    cur.execute(
        "INSERT INTO users (id, email, username, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, req.email, req.username, password_hash, now)
    )
    
    # Create tokens
    access_token = create_access_token(user_id, req.email, req.username)
    refresh_token, token_hash, expires_at = create_refresh_token()
    
    cur.execute(
        "INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at, created_at) VALUES (?, ?, ?, ?, ?)",
        (secrets.token_urlsafe(8), user_id, token_hash, expires_at, now)
    )
    
    conn.commit()
    conn.close()
    
    return JSONResponse(status_code=201, content=api_success({
        "user": {
            "id": user_id,
            "email": req.email,
            "username": req.username,
            "plan": "free",
            "plan_expires_at": None,
            "active_devices_count": 0
        },
        "access_token": access_token,
        "refresh_token": refresh_token
    }))


@router.post("/login")
async def login(req: LoginRequest) -> JSONResponse:
    """Login with email and password."""
    conn = get_db()
    cur = conn.cursor()
    
    row = cur.execute(
        "SELECT id, email, username, password_hash, plan, plan_expires_at FROM users WHERE email = ?",
        (req.email,)
    ).fetchone()
    
    if not row or not verify_password(req.password, row["password_hash"]):
        conn.close()
        return api_error("INVALID_CREDENTIALS", "Invalid email or password", 401)
    
    user_id = row["id"]
    
    # Count active devices
    device_count = cur.execute(
        "SELECT COUNT(*) FROM devices WHERE owner_user_id = ?", (user_id,)
    ).fetchone()[0]
    
    # Create tokens
    access_token = create_access_token(user_id, row["email"], row["username"])
    refresh_token, token_hash, expires_at = create_refresh_token()
    now = utc_now_iso()
    
    cur.execute(
        "INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at, created_at) VALUES (?, ?, ?, ?, ?)",
        (secrets.token_urlsafe(8), user_id, token_hash, expires_at, now)
    )
    
    conn.commit()
    conn.close()
    
    return JSONResponse(api_success({
        "user": {
            "id": user_id,
            "email": row["email"],
            "username": row["username"],
            "plan": row["plan"] or "free",
            "plan_expires_at": row["plan_expires_at"],
            "active_devices_count": device_count
        },
        "access_token": access_token,
        "refresh_token": refresh_token
    }))


@router.post("/refresh")
async def refresh(req: RefreshRequest) -> JSONResponse:
    """Refresh access token."""
    import hashlib
    
    conn = get_db()
    cur = conn.cursor()
    
    token_hash = hashlib.sha256(req.refresh_token.encode()).hexdigest()
    
    row = cur.execute(
        """SELECT rt.user_id, u.email, u.username 
           FROM refresh_tokens rt 
           JOIN users u ON rt.user_id = u.id
           WHERE rt.token_hash = ? AND rt.revoked = 0 AND rt.expires_at > datetime('now')""",
        (token_hash,)
    ).fetchone()
    
    if not row:
        conn.close()
        return api_error("INVALID_TOKEN", "Refresh token invalid or expired", 401)
    
    conn.close()
    
    access_token = create_access_token(row["user_id"], row["email"], row["username"])
    
    return JSONResponse(api_success({"access_token": access_token}))
