"""
Pydantic schemas for API request/response validation.
"""
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr


# ==================== AUTH ====================

class RegisterRequest(BaseModel):
    email: str
    password: str
    username: str


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    plan: str = "free"
    plan_expires_at: Optional[str] = None
    active_devices_count: int = 0


class AuthResponse(BaseModel):
    ok: bool = True
    user: UserResponse
    access_token: str
    refresh_token: str


class RefreshResponse(BaseModel):
    ok: bool = True
    access_token: str


# ==================== USER ====================

class UserProfile(BaseModel):
    id: str
    username: str
    email: str
    created_at: str
    plan: str = "free"
    plan_expires_at: Optional[str] = None
    active_devices_count: int = 0
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


# ==================== DEVICES ====================

class DeviceResponse(BaseModel):
    id: str
    name: str
    type: str = "cloud"
    status: str = "offline"
    vcpu: int = 2
    ram_gb: int = 4
    description: Optional[str] = None
    is_trusted: bool = False
    last_seen_at: Optional[str] = None


class DeviceListResponse(BaseModel):
    ok: bool = True
    devices: List[DeviceResponse]


# ==================== TRUSTED ====================

class TrustedAddRequest(BaseModel):
    device_id: str


# ==================== REMOTE ====================

class RemoteRequestBody(BaseModel):
    device_id: str
    password: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    state: str
    host_device_id: str
    client_user_id: str
    created_at: str
    signaling_url: Optional[str] = None
    turn_credentials: Optional[dict] = None


class PasswordVerifyRequest(BaseModel):
    device_id: str
    password: str


# ==================== PLANS ====================

class PlanResponse(BaseModel):
    code: str
    name: str
    price_usd: float
    billing_period: str = "month"
    vcpu: int
    ram_gb: int
    features: List[str] = []


# ==================== NOTIFICATIONS ====================

class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    body: Optional[str] = None
    data: Optional[dict] = None
    read: bool = False
    created_at: str
