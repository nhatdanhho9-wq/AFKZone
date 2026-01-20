"""
Admin router - manage notifications, plans, devices for demo/testing.
"""
import secrets
import json
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db
from app.utils import api_success, api_error, utc_now_iso, hash_password

router = APIRouter()


# ==================== SCHEMAS ====================

class NotificationCreate(BaseModel):
    type: str  # "promo" | "update" | "guide"
    title: str
    body: Optional[str] = None
    data: Optional[dict] = None
    user_id: Optional[str] = None  # None = global notification


class PlanUpdate(BaseModel):
    code: str
    name: Optional[str] = None
    price_usd: Optional[float] = None
    vcpu: Optional[int] = None
    ram_gb: Optional[int] = None
    features: Optional[List[str]] = None


class DeviceCreate(BaseModel):
    owner_user_id: str
    name: str
    type: str = "cloud"
    status: str = "online"
    vcpu: int = 2
    ram_gb: int = 4
    description: Optional[str] = None
    remote_password: Optional[str] = None


class DeviceStatusUpdate(BaseModel):
    status: str  # "online" | "idle" | "offline" | "error"


# ==================== NOTIFICATIONS ====================

@router.post("/notifications")
async def create_notification(req: NotificationCreate) -> JSONResponse:
    """Create a new notification."""
    conn = get_db()
    cur = conn.cursor()
    
    notif_id = secrets.token_urlsafe(12)
    now = utc_now_iso()
    data_json = json.dumps(req.data) if req.data else None
    
    cur.execute(
        "INSERT INTO notifications (id, user_id, type, title, body, data, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (notif_id, req.user_id, req.type, req.title, req.body, data_json, now)
    )
    conn.commit()
    conn.close()
    
    return JSONResponse(status_code=201, content=api_success({
        "notification": {
            "id": notif_id,
            "type": req.type,
            "title": req.title,
            "body": req.body,
            "created_at": now
        }
    }))


@router.put("/notifications/{notification_id}")
async def update_notification(notification_id: str, req: NotificationCreate) -> JSONResponse:
    """Update a notification."""
    conn = get_db()
    cur = conn.cursor()
    
    data_json = json.dumps(req.data) if req.data else None
    
    cur.execute(
        "UPDATE notifications SET type = ?, title = ?, body = ?, data = ? WHERE id = ?",
        (req.type, req.title, req.body, data_json, notification_id)
    )
    conn.commit()
    conn.close()
    
    return JSONResponse(api_success({"notification_id": notification_id, "updated": True}))


@router.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: str) -> JSONResponse:
    """Delete a notification."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM notifications WHERE id = ?", (notification_id,))
    conn.commit()
    conn.close()
    
    return JSONResponse(api_success({"deleted": True}))


# ==================== PLANS ====================

@router.put("/plans/{plan_code}")
async def update_plan(plan_code: str, req: PlanUpdate) -> JSONResponse:
    """Update a plan."""
    conn = get_db()
    cur = conn.cursor()
    
    updates = []
    params = []
    
    if req.name:
        updates.append("name = ?")
        params.append(req.name)
    if req.price_usd is not None:
        updates.append("price_usd = ?")
        params.append(req.price_usd)
    if req.vcpu is not None:
        updates.append("vcpu = ?")
        params.append(req.vcpu)
    if req.ram_gb is not None:
        updates.append("ram_gb = ?")
        params.append(req.ram_gb)
    if req.features is not None:
        updates.append("features = ?")
        params.append(json.dumps(req.features))
    
    if updates:
        params.append(plan_code)
        cur.execute(f"UPDATE plans SET {', '.join(updates)} WHERE code = ?", params)
        conn.commit()
    
    conn.close()
    
    return JSONResponse(api_success({"plan_code": plan_code, "updated": True}))


# ==================== DEVICES ====================

@router.post("/devices")
async def create_device(req: DeviceCreate) -> JSONResponse:
    """Create a device for demo/testing."""
    conn = get_db()
    cur = conn.cursor()
    
    device_id = secrets.token_urlsafe(12)
    now = utc_now_iso()
    password_hash = hash_password(req.remote_password) if req.remote_password else None
    
    cur.execute(
        """INSERT INTO devices 
           (id, owner_user_id, name, type, status, vcpu, ram_gb, description, remote_password_hash, last_seen_at, created_at) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (device_id, req.owner_user_id, req.name, req.type, req.status, 
         req.vcpu, req.ram_gb, req.description, password_hash, now, now)
    )
    conn.commit()
    conn.close()
    
    return JSONResponse(status_code=201, content=api_success({
        "device": {
            "id": device_id,
            "name": req.name,
            "type": req.type,
            "status": req.status,
            "vcpu": req.vcpu,
            "ram_gb": req.ram_gb
        }
    }))


@router.patch("/devices/{device_id}/status")
async def update_device_status(device_id: str, req: DeviceStatusUpdate) -> JSONResponse:
    """Update device status."""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute(
        "UPDATE devices SET status = ?, last_seen_at = ? WHERE id = ?",
        (req.status, utc_now_iso(), device_id)
    )
    conn.commit()
    conn.close()
    
    return JSONResponse(api_success({"device_id": device_id, "status": req.status}))


# ==================== SEED DATA ====================

@router.post("/seed")
async def seed_demo_data() -> JSONResponse:
    """Seed demo data for testing."""
    conn = get_db()
    cur = conn.cursor()
    
    now = utc_now_iso()
    
    # Get demo user
    demo_user = cur.execute("SELECT id FROM users WHERE email = 'demo@afkzone.io'").fetchone()
    if not demo_user:
        conn.close()
        return api_error("NO_DEMO_USER", "Please register demo@afkzone.io first", 400)
    
    user_id = demo_user["id"]
    
    # Seed devices
    devices = [
        ("dev_cloud01", user_id, "CLOUD_UNIT_01", "cloud", "online", 2, 4, "Basic Cloud Instance"),
        ("dev_home_pc", user_id, "HOME_PC_RYZEN", "pc", "idle", 8, 32, "Ryzen 7 5800X, 32GB RAM"),
        ("dev_mac_mini", user_id, "OFFICE_MAC_MINI", "mac", "offline", 4, 8, "Mac Mini M1"),
    ]
    for d in devices:
        cur.execute(
            """INSERT OR REPLACE INTO devices 
               (id, owner_user_id, name, type, status, vcpu, ram_gb, description, last_seen_at, created_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (*d, now, now)
        )
    
    # Seed notifications
    notifications = [
        ("notif_promo1", None, "promo", "VIP SERVER RESTOCK - GET IT NOW", 
         "Limited time offer! Secure your high-performance VIP server with massive discounts. Don't miss out, Operator.",
         '{"action": "claim_offer", "discount": 50}'),
        ("notif_update1", None, "update", "System Maintenance v2.1",
         "Optimized connection for Genshin Impact, reduced latency across all nodes, and security patches applied. Reboot recommended.",
         None),
        ("notif_guide1", None, "guide", "How to set up Macro Auto-Click",
         "Master the art of automation. Learn to configure advanced macro sequences for efficient farming. Step-by-step tutorial inside.",
         '{"url": "/guides/macro-autoclick"}'),
    ]
    for n in notifications:
        cur.execute(
            "INSERT OR REPLACE INTO notifications (id, user_id, type, title, body, data, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (*n, now)
        )
    
    conn.commit()
    conn.close()
    
    return JSONResponse(api_success({
        "seeded": {
            "devices": 3,
            "notifications": 3
        }
    }))
