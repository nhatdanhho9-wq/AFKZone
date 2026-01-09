"""
AFKZone vNext - Pydantic Models for Remote MVP v0.1
"""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


# ==================== AUTH ====================

class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)
    # Device auto-registration on login
    device_id: Optional[str] = Field(default=None, max_length=128)
    device_name: Optional[str] = Field(default=None, max_length=128)
    device_type: str = Field(default="android", max_length=32)
    # For account switch: previous device to invalidate
    previous_device_id: Optional[str] = Field(default=None, max_length=128)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    account_id: str
    expires_in: int = 86400
    # Device registered during login
    device_id: Optional[str] = None
    # Flag if account switched (old device cleared)
    account_switched: bool = False


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


# ==================== DEVICES ====================

class DeviceRegisterRequest(BaseModel):
    # Allow server-assigned device_id (prevents LDPlayer clone collisions)
    device_id: Optional[str] = Field(default=None, min_length=1, max_length=128)
    device_name: str = Field(min_length=1, max_length=128)
    device_type: str = Field(default="android", max_length=32)


class DeviceInfo(BaseModel):
    device_id: str
    device_name: str
    device_type: str
    online: bool
    last_seen: Optional[str] = None
    unattended_mode: str = "disabled"
    # Metadata (per-account personalization)
    display_name: Optional[str] = None  # User-friendly name
    is_favorite: bool = False
    always_relay: bool = False  # Force TURN relay


class DeviceUpdateRequest(BaseModel):
    """Update device metadata (PATCH /devices/{id})."""
    display_name: Optional[str] = Field(default=None, max_length=128)
    is_favorite: Optional[bool] = None
    always_relay: Optional[bool] = None


class DeviceListResponse(BaseModel):
    devices: List[DeviceInfo]


class HeartbeatRequest(BaseModel):
    """Device heartbeat with optional source for TTL tracking."""
    source: str = Field(default="foreground", pattern="^(foreground|background|service)$")
    # foreground: app is active on screen
    # background: app is in background but still running
    # service: background service heartbeat (may be killed by OS)


class HeartbeatResponse(BaseModel):
    ok: bool
    server_time: str
    next_interval_ms: int = 30000  # Suggest 30s heartbeat interval


# ==================== TRUSTED ALLOWLIST ====================

class TrustedEntry(BaseModel):
    id: int
    target_device_id: str
    requester_account_id: Optional[str]
    requester_device_id: Optional[str]
    status: str
    created_at: str
    approved_at: Optional[str]


class TrustedListResponse(BaseModel):
    entries: List[TrustedEntry]


class TrustedRequestCreate(BaseModel):
    """Controller requests trust to access a device."""
    target_device_id: str = Field(min_length=1, max_length=128)
    requester_device_id: Optional[str] = None


class TrustedApproveRequest(BaseModel):
    """Owner approves a trust request. If trust=True, save controller device pair for auto-approve."""
    request_id: int
    trust: bool = False  # If True, save device pair for future auto-approve


class TrustedRevokeRequest(BaseModel):
    """Owner revokes trust."""
    entry_id: int


# ==================== SHARE TOKENS ====================

class ShareCreateRequest(BaseModel):
    device_id: str = Field(min_length=1, max_length=128)
    expires_hours: int = Field(default=24, ge=1, le=168)  # 1 hour to 1 week
    max_uses: int = Field(default=1, ge=1, le=100)
    # Which owner device created this token (for notification UX)
    created_by_device_id: Optional[str] = None


class ShareCreateResponse(BaseModel):
    token: str  # 6-8 char code
    expires_at: str


class ShareResolveRequest(BaseModel):
    token: str = Field(min_length=6, max_length=8)


class ShareResolveResponse(BaseModel):
    device_id: str
    device_name: str
    account_id: str  # Owner account


class ShareRevokeRequest(BaseModel):
    token: str


# ==================== REMOTE SESSIONS ====================

class RemoteRequestCreate(BaseModel):
    """Request remote session to a device."""
    target_device_id: Optional[str] = None  # If trusted
    share_token: Optional[str] = None        # Or via token
    requester_device_id: Optional[str] = None


class RemoteRequestResponse(BaseModel):
    request_id: str
    status: str  # 'pending', 'approved', 'auto_approved' (if trusted)
    session_id: Optional[str] = None  # If auto-approved
    claim_token: Optional[str] = None  # Opaque token requester uses to claim session info after approval


class RemoteRequestInfo(BaseModel):
    request_id: str
    target_device_id: str
    target_device_name: Optional[str] = None
    requester_account_id: Optional[str]
    requester_device_id: Optional[str]
    share_token: Optional[str]
    share_created_by_device_id: Optional[str] = None
    status: str
    created_at: str
    expires_at: str


class RemotePendingResponse(BaseModel):
    requests: List[RemoteRequestInfo]


class RemoteApproveRequest(BaseModel):
    request_id: str


class RemoteApproveResponse(BaseModel):
    ok: bool
    session_id: str
    signaling_ws_url: str
    # Controller token for the requester to connect to signaling WS.
    # NOTE: For MVP, owner approval creates the signaling session and returns controller_token.
    controller_token: str


class RemoteClaimRequest(BaseModel):
    request_id: str
    claim_token: str


class RemoteClaimResponse(BaseModel):
    ok: bool
    status: str
    session_id: Optional[str] = None
    signaling_ws_url: Optional[str] = None
    controller_token: Optional[str] = None
