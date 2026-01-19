"""
Utilities module with helpers for auth, database, and response formatting.
"""
import hashlib
import hmac
import secrets
import sqlite3
import base64
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Tuple

from fastapi import Depends, HTTPException, Header
from pydantic import BaseModel


# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "afkzone.db"

# JWT secret (in production, use environment variable)
JWT_SECRET = "afkzone-cleanroom-secret-key-2026"
TOKEN_EXPIRY_HOURS = 24


class TokenClaims(BaseModel):
    """JWT token claims."""
    account_id: str
    username: str
    iat: int
    exp: int


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def utc_now_iso() -> str:
    """Get current UTC time as ISO string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def hash_password(password: str) -> str:
    """Hash password using SHA256 with salt."""
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{h}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against stored hash."""
    try:
        salt, h = password_hash.split(":")
        return h == hashlib.sha256((salt + password).encode()).hexdigest()
    except (ValueError, AttributeError):
        return False


def create_access_token(account_id: str, username: str) -> Tuple[str, str]:
    """Create JWT-like access token."""
    import json
    
    iat = int(datetime.now(timezone.utc).timestamp())
    exp = iat + (TOKEN_EXPIRY_HOURS * 3600)
    
    payload = {
        "account_id": account_id,
        "username": username,
        "iat": iat,
        "exp": exp,
    }
    
    payload_json = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    
    # Sign with HMAC
    signature = hmac.new(
        JWT_SECRET.encode(),
        payload_b64.encode(),
        hashlib.sha256
    ).hexdigest()[:32]
    
    token = f"{payload_b64}.{signature}"
    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc).isoformat()
    
    return token, expires_at


def decode_token(token: str) -> Optional[TokenClaims]:
    """Decode and verify JWT-like token."""
    import json
    
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
            
        payload_b64, signature = parts
        
        # Verify signature
        expected_sig = hmac.new(
            JWT_SECRET.encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).hexdigest()[:32]
        
        if signature != expected_sig:
            return None
        
        # Decode payload
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
            
        payload_json = base64.urlsafe_b64decode(payload_b64).decode()
        payload = json.loads(payload_json)
        
        # Check expiry
        if payload.get("exp", 0) < datetime.now(timezone.utc).timestamp():
            return None
        
        return TokenClaims(**payload)
        
    except Exception:
        return None


async def get_current_user(authorization: str = Header(None)) -> TokenClaims:
    """Dependency to get current authenticated user."""
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header",
            headers={"X-Error-Code": "UNAUTHORIZED"}
        )
    
    # Extract token from "Bearer {token}"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format",
            headers={"X-Error-Code": "UNAUTHORIZED"}
        )
    
    token = parts[1]
    claims = decode_token(token)
    
    if not claims:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"X-Error-Code": "AUTH_TOKEN_EXPIRED"}
        )
    
    return claims


def api_success(data: dict = None) -> dict:
    """Standard success response."""
    return {"ok": True, "data": data}


def api_error(error_code: str, message: str, status_code: int = 400):
    """Standard error response (returns HTTPException)."""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status_code,
        content={"ok": False, "error_code": error_code, "message": message},
        headers={"X-Error-Code": error_code}
    )
