"""
Pydantic models for API request/response validation.
"""
from typing import Optional, List
from pydantic import BaseModel


# ==================== AUTH ====================

class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    account_id: str
    username: str
    created_at: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400
    user: UserInfo


# ==================== DEVICES ====================

class DeviceRegisterRequest(BaseModel):
    device_id: Optional[str] = None
    device_name: str
    device_type: str = "android"


class DeviceInfo(BaseModel):
    id: str
    deviceId: str
    name: str
    type: str
    status: str
    lastSeen: Optional[str] = None
    cpu: str = "Unknown"
    ram: str = "Unknown"
    os: str = "Unknown"


class DeviceListResponse(BaseModel):
    devices: List[DeviceInfo]


# ==================== REMOTE ====================

class RemoteRequest(BaseModel):
    target_device_id: str
    requester_device_id: Optional[str] = None
    share_token: Optional[str] = None


class RemoteRequestResponse(BaseModel):
    request_id: str
    status: str
    created_at: str
    expires_at: str


class RemoteApproveRequest(BaseModel):
    request_id: str


class RemoteApproveResponse(BaseModel):
    request_id: str
    status: str
    session_id: str
    signaling_ws_url: str
    controller_token: str


# ==================== TRUSTED ====================

class TrustRequestCreate(BaseModel):
    target_device_id: str
    requester_device_id: Optional[str] = None
    label: Optional[str] = None


class TrustApproveRequest(BaseModel):
    trust_request_id: int
    allow_input_control: bool = True
    allow_file_transfer: bool = False


class TrustedDevice(BaseModel):
    trust_id: int
    device_id: str
    device_name: str
    direction: str
    permissions: dict
    created_at: str
    last_used_at: Optional[str] = None


# ==================== SESSIONS ====================

class SessionStatsRequest(BaseModel):
    ice_state: Optional[str] = None
    ice_path: Optional[str] = None
    bitrate_kbps: Optional[int] = None
    fps: Optional[int] = None


class InputControlRequest(BaseModel):
    action: str  # "start" or "stop"
    controller_device_id: Optional[str] = None


class DisconnectRequest(BaseModel):
    reason: Optional[str] = "user_initiated"


# ==================== PASSWORD ====================

class PasswordVerifyRequest(BaseModel):
    target_device_id: str
    password: str
