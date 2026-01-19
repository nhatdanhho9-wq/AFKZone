"""
Auth router - login and register endpoints.
"""
import secrets
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models import RegisterRequest, LoginRequest
from app.utils import get_db, utc_now_iso, hash_password, verify_password, create_access_token, api_success, api_error

router = APIRouter()


@router.post("/auth/register")
async def auth_register(req: RegisterRequest) -> JSONResponse:
    """Register a new account."""
    conn = get_db()
    cur = conn.cursor()
    
    # Check if username exists
    existing = cur.execute(
        "SELECT account_id FROM account WHERE username = ?",
        (req.username,)
    ).fetchone()
    
    if existing:
        conn.close()
        return api_error("USERNAME_EXISTS", "Username already exists", 409)
    
    account_id = secrets.token_urlsafe(16)
    password_hash = hash_password(req.password)
    now = utc_now_iso()
    
    cur.execute(
        "INSERT INTO account (account_id, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (account_id, req.username, password_hash, now)
    )
    conn.commit()
    conn.close()
    
    return JSONResponse(api_success({
        "account_id": account_id,
        "username": req.username,
        "created_at": now,
    }))


@router.post("/auth/login")
async def auth_login(req: LoginRequest) -> JSONResponse:
    """Login and get access token."""
    conn = get_db()
    cur = conn.cursor()
    
    row = cur.execute(
        "SELECT account_id, username, password_hash, created_at FROM account WHERE username = ?",
        (req.username,)
    ).fetchone()
    conn.close()
    
    if not row or not verify_password(req.password, row["password_hash"]):
        return api_error("AUTH_INVALID_CREDENTIALS", "Invalid username or password", 401)
    
    token, expires_at = create_access_token(row["account_id"], row["username"])
    
    return JSONResponse(api_success({
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 86400,
        "user": {
            "account_id": row["account_id"],
            "username": row["username"],
            "created_at": row["created_at"],
        }
    }))
