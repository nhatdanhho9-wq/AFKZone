"""
Utility functions for auth, security, and helpers.
"""
import hashlib
import hmac
import secrets
import base64
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from fastapi import Depends, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import JWT_SECRET, ACCESS_TOKEN_TTL, REFRESH_TOKEN_TTL, TURN_SECRET, TURN_HOST


class TokenClaims(BaseModel):
    """JWT token claims."""
    user_id: str
    email: str
    username: str
    iat: int
    exp: int


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def hash_password(password: str) -> str:
    """Hash password with salt."""
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{h}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    try:
        salt, h = password_hash.split(":")
        return h == hashlib.sha256((salt + password).encode()).hexdigest()
    except:
        return False


def create_access_token(user_id: str, email: str, username: str) -> str:
    """Create JWT access token."""
    iat = int(utc_now().timestamp())
    exp = iat + ACCESS_TOKEN_TTL
    
    payload = {"user_id": user_id, "email": email, "username": username, "iat": iat, "exp": exp}
    payload_json = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    
    signature = hmac.new(JWT_SECRET.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{payload_b64}.{signature}"


def create_refresh_token() -> Tuple[str, str, str]:
    """Create refresh token. Returns (token, token_hash, expires_at)."""
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = (utc_now() + timedelta(seconds=REFRESH_TOKEN_TTL)).isoformat()
    return token, token_hash, expires_at


def decode_token(token: str) -> Optional[TokenClaims]:
    """Decode and verify JWT token."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        
        payload_b64, signature = parts
        expected_sig = hmac.new(JWT_SECRET.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()[:32]
        
        if signature != expected_sig:
            return None
        
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode())
        
        if payload.get("exp", 0) < utc_now().timestamp():
            return None
        
        return TokenClaims(**payload)
    except:
        return None


async def get_current_user(authorization: str = Header(None)) -> TokenClaims:
    """Dependency to get current authenticated user."""
    if not authorization:
        raise HTTPException(status_code=401, detail={"ok": False, "error_code": "UNAUTHORIZED", "message": "Missing Authorization header"})
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail={"ok": False, "error_code": "UNAUTHORIZED", "message": "Invalid Authorization format"})
    
    claims = decode_token(parts[1])
    if not claims:
        raise HTTPException(status_code=401, detail={"ok": False, "error_code": "TOKEN_EXPIRED", "message": "Token invalid or expired"})
    
    return claims


def api_success(data: dict = None) -> dict:
    """Standard success response."""
    if data is None:
        return {"ok": True}
    return {"ok": True, **data}


def api_error(error_code: str, message: str, status_code: int = 400) -> JSONResponse:
    """Standard error response."""
    return JSONResponse(
        status_code=status_code,
        content={"ok": False, "error_code": error_code, "message": message}
    )


def mint_turn_credentials(session_id: str) -> dict:
    """Generate TURN credentials."""
    timestamp = int(time.time()) + 86400
    username = f"{timestamp}:{session_id}"
    credential = hashlib.sha1(f"{TURN_SECRET}{username}".encode()).hexdigest()[:24]
    
    return {
        "urls": [f"turn:{TURN_HOST}:3478"],
        "username": username,
        "credential": credential
    }
