"""
AFKZone vNext - JWT Authentication Helper for Remote MVP v0.1
Simple JWT-based auth for MVP. Replace with proper auth service later.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request

# JWT secret (should be set in environment for production)
JWT_SECRET = os.getenv("AFK_JWT_SECRET", "dev-jwt-secret-change-in-prod")
JWT_EXPIRY = 86400  # 24 hours


@dataclass
class TokenClaims:
    """JWT claims after verification."""
    account_id: str
    username: str
    issued_at: int
    expires_at: int


def _utc_now() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def hash_password(password: str) -> str:
    """Simple password hashing for MVP. Use bcrypt in production."""
    salt = os.getenv("AFK_PASSWORD_SALT", "afkzone-dev-salt")
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == password_hash


def create_access_token(account_id: str, username: str) -> tuple[str, int]:
    """
    Create a simple JWT-like token.
    Returns (token, expires_at timestamp).
    """
    now = _utc_now()
    expires_at = now + JWT_EXPIRY
    
    payload = {
        "account_id": account_id,
        "username": username,
        "iat": now,
        "exp": expires_at,
    }
    
    # Simple base64(json) + HMAC signature
    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    ).decode().rstrip("=")
    
    sig = hmac.new(
        JWT_SECRET.encode(),
        payload_b64.encode(),
        hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode().rstrip("=")
    
    token = f"{payload_b64}.{sig_b64}"
    return token, expires_at


def verify_access_token(token: str) -> Optional[TokenClaims]:
    """
    Verify token and return claims if valid.
    Returns None if invalid or expired.
    """
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        
        payload_b64, sig_b64 = parts
        
        # Verify signature
        expected_sig = hmac.new(
            JWT_SECRET.encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).digest()
        
        # Pad base64 if needed
        sig_b64_padded = sig_b64 + "=" * (4 - len(sig_b64) % 4)
        actual_sig = base64.urlsafe_b64decode(sig_b64_padded)
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        
        # Decode payload
        payload_b64_padded = payload_b64 + "=" * (4 - len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64_padded).decode()
        payload = json.loads(payload_json)
        
        # Check expiry
        if payload["exp"] < _utc_now():
            return None
        
        return TokenClaims(
            account_id=payload["account_id"],
            username=payload["username"],
            issued_at=payload["iat"],
            expires_at=payload["exp"],
        )
    except Exception:
        return None


def get_current_user(request: Request) -> TokenClaims:
    """
    FastAPI dependency to get current authenticated user.
    Raises HTTPException 401 if not authenticated.
    """
    auth = request.headers.get("Authorization", "")
    
    if not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth.split(" ", 1)[1]
    claims = verify_access_token(token)
    
    if not claims:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return claims


def get_optional_user(request: Request) -> Optional[TokenClaims]:
    """
    Get user if authenticated, None otherwise.
    For endpoints that work both authenticated and anonymous.
    """
    auth = request.headers.get("Authorization", "")
    
    if not auth.startswith("Bearer "):
        return None
    
    token = auth.split(" ", 1)[1]
    return verify_access_token(token)


def generate_token_code(length: int = 6) -> str:
    """Generate a random alphanumeric code for share tokens."""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # Avoid confusing chars
    return "".join(secrets.choice(chars) for _ in range(length))
