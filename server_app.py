import os
from dotenv import load_dotenv

load_dotenv()
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Tier to max_devices mapping
TIER_MAX_DEVICES = {
    'basic': 2,
    'pro': 5,
    'enterprise': -1  # unlimited
}

def get_max_devices_for_tier(tier: str) -> int:
    return TIER_MAX_DEVICES.get(tier.lower(), 1)
from pydantic import BaseModel
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
import hashlib
import secrets
import hmac
import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()
import json
import base64
from database import get_db

def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set")
    return value

def to_iso(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000).isoformat()
    value_str = str(value)
    if value_str.isdigit():
        return datetime.fromtimestamp(int(value_str) / 1000).isoformat()
    try:
        return datetime.fromisoformat(value_str).isoformat()
    except ValueError:
        return value_str

def to_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000)
    value_str = str(value)
    if value_str.isdigit():
        return datetime.fromtimestamp(int(value_str) / 1000)
    try:
        return datetime.fromisoformat(value_str)
    except ValueError:
        return None

ADMIN_KEY = require_env("ADMIN_KEY")
# Support both names (docker-compose uses JWT_SECRET_KEY)
JWT_SECRET = os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET or JWT_SECRET_KEY is not set")
CASSO_WEBHOOK_TOKEN = require_env("CASSO_WEBHOOK_TOKEN")

app = FastAPI(title="AFK Zone License API v2.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
SERVER_CONFIGS = {
    "id_server": "id.afkzone.cloud",
    "relay_server": "id.afkzone.cloud",
    "public_key": "EXOW136uTrC0PYYrkavoJH7SjkFlzPjB+vzzpvjsybw=",
    "api_server": "https://api.afkzone.cloud"
}

# ==================== GLOBAL EXCEPTION HANDLERS ====================
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code = "HTTP_ERROR"
    if exc.status_code == 401: code = "UNAUTHORIZED"
    elif exc.status_code == 403: code = "FORBIDDEN"
    elif exc.status_code == 404: code = "NOT_FOUND" 
    elif exc.status_code == 400: code = "INVALID_INPUT"
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": code,
            "error": code,
            "message": exc.detail,
            "detail": str(exc.detail)
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "INTERNAL_ERROR",
            "error": "INTERNAL_ERROR",
            "message": "Internal Server Error",
            "detail": str(exc)
        }
    )

DEVICE_LIMITS = {"basic": 2, "pro": 5, "enterprise": -1}

ZALOPAY_CONFIG = {
    "app_id": int(require_env("ZALOPAY_APP_ID")),
    "key1": require_env("ZALOPAY_KEY1"),
    "key2": require_env("ZALOPAY_KEY2"),
    "endpoint": require_env("ZALOPAY_ENDPOINT")
}

class ActivateRequest(BaseModel):
    license_key: str
    device_id: str

class GenerateRequest(BaseModel):
    tier: str
    duration_days: int
    quantity: int = 1

class TrialGenerateRequest(BaseModel):
    device_fingerprint: str
    ip_address: Optional[str] = None

class PaymentCreateRequest(BaseModel):
    tier: str
    duration_days: int
    device_id: str

@app.get("/")
def root():
    return {"service": "AFK Zone License API", "version": "2.2.0", "contact": "Zalo: 0823333374"}

@app.post("/activate")
def activate_license(data: dict, db: Session = Depends(get_db)):
    """Activate license on a device - supports multi-device"""
    license_key = data.get("license_key")
    device_id = data.get("device_id")
    
    if not license_key or not device_id:
        raise HTTPException(status_code=400, detail="Missing license_key or device_id")
    
    # Check if license exists
    lic = db.execute(
        text("SELECT license_key, tier, duration_days, activated_at, expires_at, max_devices, is_revoked FROM licenses WHERE license_key=:key"),
        {"key": license_key}
    ).fetchone()
    
    if not lic:
        raise HTTPException(status_code=404, detail="License không hợp lệ")
    
    if lic[6]:  # is_revoked
        raise HTTPException(status_code=403, detail="License đã bị thu hồi")
    
    max_devices = lic[5] if lic[5] else 1
    
    # Check if device is already activated with this license
    existing = db.execute(
        text("SELECT id FROM license_devices WHERE license_key=:key AND device_id=:device"),
        {"key": license_key, "device": device_id}
    ).fetchone()
    
    if existing:
        # Device already activated - return success
        return {
            "status": "active",
            "tier": lic[1],
            "duration_days": lic[2],
            "expires_at": to_iso(lic[4]),
            "max_devices": max_devices,
            "message": "Device đã được kích hoạt trước đó"
        }
    
    # Count current activated devices
    device_count = db.execute(
        text("SELECT COUNT(*) FROM license_devices WHERE license_key=:key"),
        {"key": license_key}
    ).scalar() or 0
    
    # Check if max devices reached (skip check if max_devices = -1 = unlimited)
    if max_devices != -1 and device_count >= max_devices:
        raise HTTPException(
            status_code=400, 
            detail=f"License đã đạt giới hạn {max_devices} thiết bị. Vui lòng xóa thiết bị cũ hoặc nâng cấp gói."
        )
    
    # Activate on this device
    try:
        db.execute(
            text("INSERT INTO license_devices (license_key, device_id, activated_at) VALUES (:key, :device, NOW())"),
            {"key": license_key, "device": device_id}
        )
        
        # If this is a trial license, also mark device in trial_devices to prevent generating new trials
        if license_key.startswith('AFK-TRIAL-'):
            # Check if device already in trial_devices
            existing_trial = db.execute(
                text("SELECT id FROM trial_devices WHERE device_fingerprint=:device"),
                {"device": device_id}
            ).fetchone()
            
            if not existing_trial:
                # Get IP address from request (if available) or use device_id
                # Insert into trial_devices to mark this device as having used a trial
                try:
                    db.execute(
                        text("INSERT INTO trial_devices (device_fingerprint, license_key, created_at) VALUES (:device, :key, NOW())"),
                        {"device": device_id, "key": license_key}
                    )
                except Exception as e:
                    # Ignore duplicate errors, just log
                    print(f"Warning: Could not insert into trial_devices: {e}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add device: {str(e)}")
    
    # Update activated_at if first activation
    if not lic[3]:  # activated_at is NULL
        expires_at = datetime.now() + timedelta(days=lic[2])
        db.execute(
            text("UPDATE licenses SET activated_at=NOW(), expires_at=:exp WHERE license_key=:key"),
            {"key": license_key, "exp": expires_at}
        )
        db.commit()
        return {
            "status": "activated",
            "tier": lic[1],
            "duration_days": lic[2],
            "expires_at": expires_at.isoformat(),
            "max_devices": max_devices,
            "device_count": device_count + 1,
            "message": "Kích hoạt thành công!"
        }
    
    db.commit()
    return {
        "status": "activated",
        "tier": lic[1],
        "duration_days": lic[2],
        "expires_at": to_iso(lic[4]),
        "max_devices": max_devices,
        "device_count": device_count + 1,
        "message": "Thêm thiết bị thành công!"
    }

@app.post("/check")
def check_license(req: ActivateRequest, db: Session = Depends(get_db)):
    """Check if license is valid for this device"""

    # Use license_devices table
    r = db.execute(
        text("""
            SELECT l.tier, l.expires_at, l.max_devices
            FROM licenses l
            JOIN license_devices ld ON l.license_key = ld.license_key
            WHERE l.license_key=:k AND ld.device_id=:d AND ld.is_active=TRUE
        """),
        {"k": req.license_key, "d": req.device_id}
    ).fetchone()

    if not r:
        raise HTTPException(404, "License không hợp lệ")

    exp = to_datetime(r[1])
    if not exp:
        raise HTTPException(status_code=500, detail="Invalid expires_at")
    if datetime.now() > exp:
        raise HTTPException(410, "Đã hết hạn")

    # Update last_check
    db.execute(
        text("UPDATE license_devices SET last_check=NOW() WHERE license_key=:k AND device_id=:d"),
        {"k": req.license_key, "d": req.device_id}
    )
    db.commit()

    return {
        "status": "active",
        "tier": r[0],
        "expires_at": to_iso(exp),
        "device_limit": r[2],
        **SERVER_CONFIGS
    }

@app.post("/generate")
def generate_licenses(req: GenerateRequest, admin_key: str = Header(None), db: Session = Depends(get_db)):
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if req.tier not in DEVICE_LIMITS or req.duration_days not in [7, 30, 60, 90, 180, 365]:
        raise HTTPException(status_code=400, detail="Invalid tier or duration")
    keys = []
    for _ in range(req.quantity):
        key = f"AFK-{secrets.token_hex(8).upper()}"
        db.execute(text("INSERT INTO licenses (license_key, tier, duration_days, created_at, is_trial) VALUES (:key, :tier, :dur, NOW(), FALSE)"),
                  {"key": key, "tier": req.tier, "dur": req.duration_days})
        keys.append(key)
    db.commit()
    return {"generated": len(keys), "keys": keys, "tier": req.tier, "duration_days": req.duration_days}

@app.get("/list")
def list_licenses(admin_key: str = Header(None), db: Session = Depends(get_db)):
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    results = db.execute(text("SELECT * FROM licenses ORDER BY created_at DESC LIMIT 100")).fetchall()
    licenses = [{"license_key": r[1], "tier": r[2], "duration_days": r[3], "activated_at": to_iso(r[4]),
                 "expires_at": to_iso(r[5]), "device_id": r[6], "is_trial": r[11]} for r in results]
    return {"total": len(licenses), "licenses": licenses}

@app.post("/trial/generate")
def trial_generate(req: TrialGenerateRequest, request: Request, db: Session = Depends(get_db)):
    ip = req.ip_address or request.client.host
    existing = db.execute(text("SELECT * FROM trial_devices WHERE device_fingerprint=:fp"), {"fp": req.device_fingerprint}).fetchone()
    if existing:
        raise HTTPException(status_code=403, detail="Bạn đã dùng thử rồi. Liên hệ Zalo: 0823333374")
    key = f"AFK-TRIAL-{secrets.token_hex(8).upper()}"
    now = datetime.now()
    expires = now + timedelta(days=7)
    db.execute(text("INSERT INTO licenses (license_key, tier, duration_days, activated_at, expires_at, device_fingerprint, created_at, is_trial, last_check) VALUES (:key, 'basic', 7, :now, :exp, :fp, :now, TRUE, :now)"),
              {"key": key, "now": now, "exp": expires, "fp": req.device_fingerprint})
    db.execute(text("INSERT INTO trial_devices (device_fingerprint, ip_address, license_key, created_at) VALUES (:fp, :ip, :key, :now)"),
              {"fp": req.device_fingerprint, "ip": ip, "key": key, "now": now})
    db.commit()
    return {"license_key": key, "tier": "basic", "expires_at": expires.isoformat(), "device_limit": 1, "message": "Bạn đã kích hoạt dùng thử 7 ngày", **SERVER_CONFIGS}

@app.post("/trial/check")
def trial_check(req: TrialGenerateRequest, db: Session = Depends(get_db)):
    result = db.execute(text("SELECT * FROM trial_devices WHERE device_fingerprint=:fp"), {"fp": req.device_fingerprint}).fetchone()
    return {"has_trialed": bool(result), "trial_date": to_iso(result[4]) if result else None}

@app.post("/payment/create")
def payment_create(req: PaymentCreateRequest, db: Session = Depends(get_db)):
    price_result = db.execute(text("SELECT price FROM pricing WHERE tier=:tier AND duration_days=:days"),
                             {"tier": req.tier, "days": req.duration_days}).fetchone()
    if not price_result:
        raise HTTPException(status_code=400, detail="Invalid tier or duration")
    price = price_result[0]
    trans_id = f"{datetime.now().strftime('%y%m%d')}_{int(time.time())}"
    order = {
        "app_id": ZALOPAY_CONFIG["app_id"],
        "app_trans_id": trans_id,
        "app_user": req.device_id,
        "app_time": int(time.time() * 1000),
        "amount": price,
        "item": json.dumps([{"itemid":"license","itemname":f"AFK Zone {req.tier} {req.duration_days}d","itemprice":price,"itemquantity":1}]),
        "embed_data": json.dumps({"tier": req.tier, "duration_days": req.duration_days, "device_id": req.device_id}),
        "callback_url": "https://api.afkzone.cloud/payment/callback",
        "description": f"AFK Zone License {req.tier}",
        "bank_code": ""
    }
    data = f"{order['app_id']}|{order['app_trans_id']}|{order['app_user']}|{order['amount']}|{order['app_time']}|{order['embed_data']}|{order['item']}"
    order["mac"] = hmac.new(ZALOPAY_CONFIG["key1"].encode(), data.encode(), hashlib.sha256).hexdigest()
    response = requests.post(ZALOPAY_CONFIG["endpoint"], json=order, timeout=10)
    zp_response = response.json()
    if zp_response.get("return_code") == 1:
        db.execute(text("INSERT INTO orders (order_id, device_id, tier, duration_days, amount, zp_trans_token, zp_order_url, payment_status) VALUES (:id, :dev, :tier, :dur, :amt, :token, :url, 'pending')"),
                  {"id": trans_id, "dev": req.device_id, "tier": req.tier, "dur": req.duration_days, "amt": price, "token": zp_response.get("zp_trans_token"), "url": zp_response.get("order_url")})
        db.commit()
        return {"order_id": trans_id, "amount": price, "zp_trans_token": zp_response.get("zp_trans_token"), "order_url": zp_response.get("order_url")}
    raise HTTPException(status_code=500, detail=f"ZaloPay error: {zp_response.get('return_message')}")

@app.post("/payment/callback")
async def payment_callback(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        mac = hmac.new(ZALOPAY_CONFIG["key2"].encode(), data.get("data", "").encode(), hashlib.sha256).hexdigest()
        if mac != data.get("mac"):
            return {"return_code": -1, "return_message": "Invalid signature"}
        cb_data = json.loads(data.get("data", "{}"))
        app_trans_id = cb_data.get("app_trans_id")
        order = db.execute(text("SELECT * FROM orders WHERE order_id=:id"), {"id": app_trans_id}).fetchone()
        if not order or order[8] == "success":
            return {"return_code": 1, "return_message": "Already processed"}
        key = f"AFK-{secrets.token_hex(8).upper()}"
        now = datetime.now()
        expires = now + timedelta(days=order[5])
        db.execute(text("INSERT INTO licenses (license_key, tier, duration_days, activated_at, expires_at, device_id, created_at, is_trial, last_check) VALUES (:key, :tier, :dur, :now, :exp, :dev, :now, FALSE, :now)"),
                  {"key": key, "tier": order[3], "dur": order[5], "now": now, "exp": expires, "dev": order[2]})
        db.execute(text("UPDATE orders SET payment_status='success', paid_at=:now, license_key=:key WHERE order_id=:id"),
                  {"now": now, "key": key, "id": app_trans_id})
        db.commit()
        return {"return_code": 1, "return_message": "success"}
    except Exception as e:
        return {"return_code": 0, "return_message": str(e)}

@app.get("/version/check")
def version_check(current: str, db: Session = Depends(get_db)):
    latest = db.execute(text("SELECT * FROM app_versions WHERE is_latest=TRUE LIMIT 1")).fetchone()
    if not latest:
        return {"has_update": False}
    return {"current_version": current, "latest_version": latest[1], "has_update": current != latest[1],
            "force_update": latest[6], "download_url": latest[3], "changelog": latest[4]}

@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except:
        return {"status": "unhealthy", "database": "disconnected"}

# Bank Transfer Configuration
BANK_CONFIG = {
    "bank_id": "970422",
    "account_no": require_env("MB_BANK_ACCOUNT"),
    "account_name": require_env("MB_BANK_NAME"),
    "casso_token": CASSO_WEBHOOK_TOKEN
}

class BankTransferRequest(BaseModel):
    tier: str
    duration_days: int
    device_id: str

@app.post("/payment/bank/create")
def bank_transfer_create(req: BankTransferRequest, db: Session = Depends(get_db)):
    # First try products table (for admin-created products)
    price_result = db.execute(text("SELECT price FROM products WHERE tier=:tier AND duration_days=:days AND is_active=TRUE"), {"tier": req.tier, "days": req.duration_days}).fetchone()
    
    # Fallback to pricing table
    if not price_result:
        price_result = db.execute(text("SELECT price FROM pricing WHERE tier=:tier AND duration_days=:days"), {"tier": req.tier, "days": req.duration_days}).fetchone()
    
    if not price_result:
        raise HTTPException(status_code=400, detail="Invalid tier or duration")
    price, date_part = price_result[0], datetime.now().strftime("%y%m%d")
    count = (db.execute(text("SELECT COUNT(*) FROM bank_orders WHERE trans_code LIKE :pattern"), {"pattern": f"AFK{req.tier.upper()}{req.duration_days}{date_part}%"}).fetchone() or (0,))[0]
    trans_code = f"AFK{req.tier.upper()}{req.duration_days}{date_part}{count+1:03d}"
    qr_url = f"https://img.vietqr.io/image/{BANK_CONFIG['bank_id']}-{BANK_CONFIG['account_no']}-compact2.png?amount={price}&addInfo={trans_code}&accountName={BANK_CONFIG['account_name']}"
    db.execute(text("INSERT INTO bank_orders (trans_code,device_id,tier,duration_days,amount,bank_account,qr_url,status,created_at) VALUES (:code,:dev,:tier,:dur,:amt,:acc,:qr,'pending',NOW())"), {"code":trans_code,"dev":req.device_id,"tier":req.tier,"dur":req.duration_days,"amt":price,"acc":BANK_CONFIG['account_no'],"qr":qr_url})
    db.commit()
    return {"trans_code":trans_code,"amount":price,"qr_url":qr_url,"bank_info":{"bank_name":"MB Bank","account_no":BANK_CONFIG['account_no'],"account_name":BANK_CONFIG['account_name'],"content":trans_code},"message":f"Chuyển khoản {price:,}đ với nội dung: {trans_code}","expires_in":600}

@app.get("/payment/bank/webhook")
async def bank_webhook_test():
    """Test endpoint for Casso webhook verification"""
    return {"success": True, "message": "Webhook endpoint is ready", "return_code": 1}

@app.post("/payment/bank/webhook")
async def bank_webhook(request: Request, db: Session = Depends(get_db)):
    import re
    try:
        # DEPRECATED: Canonical endpoint is /webhook/casso
        print("⚠️ DEPRECATED ENDPOINT: /payment/bank/webhook was called. Please update to /webhook/casso")
        
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8')
        
        # DEV MODE: Accept any x-casso-signature while investigating correct algorithm
        # PRODUCTION: Set to False to enforce signature verification
        DEV_BYPASS_SIGNATURE = False  # DISABLED for production - Casso signatures must be verified
        
        signature_header = request.headers.get("x-casso-signature", "")
        secure_token = request.headers.get("secure-token", "")
        
        secret = BANK_CONFIG['casso_token']
        auth_valid = False
        
        print(f"=== CASSO WEBHOOK DEBUG ===")
        print(f"x-casso-signature present: {bool(signature_header)}")
        print(f"secure-token present: {bool(secure_token)}")
        
        if signature_header:
            # Check if signature has t=...,v1=... format
            if "t=" in signature_header and "v1=" in signature_header:
                # Casso Webhook V2: parse structured signature
                sig_parts = {}
                for part in signature_header.split(","):
                    if "=" in part:
                        k, v = part.split("=", 1)
                        sig_parts[k] = v
                
                timestamp = sig_parts.get("t", "")
                signature = sig_parts.get("v1", "")
                
                # Try SHA512 first (original)
                signed_payload = f"{timestamp}.{body_str}"
                expected_sha512 = hmac.new(secret.encode(), signed_payload.encode(), hashlib.sha512).hexdigest()
                expected_sha256 = hmac.new(secret.encode(), signed_payload.encode(), hashlib.sha256).hexdigest()
                
                print(f"Timestamp: {timestamp}")
                print(f"Signature received: {signature[:50]}...")
                print(f"Expected SHA512: {expected_sha512[:50]}...")
                print(f"Expected SHA256: {expected_sha256[:50]}...")
                
                if signature == expected_sha512 or signature == expected_sha256:
                    auth_valid = True
                    print("✅ Structured signature verified!")
            else:
                # Raw signature (no t=,v1= format) - try multiple algorithms
                signature = signature_header
                
                # Try with body_str
                expected_sha512_str = hmac.new(secret.encode(), body_str.encode(), hashlib.sha512).hexdigest()
                expected_sha256_str = hmac.new(secret.encode(), body_str.encode(), hashlib.sha256).hexdigest()
                
                # Try with raw body_bytes
                expected_sha512_bytes = hmac.new(secret.encode(), body_bytes, hashlib.sha512).hexdigest()
                expected_sha256_bytes = hmac.new(secret.encode(), body_bytes, hashlib.sha256).hexdigest()
                
                print(f"Raw signature received: {signature[:50]}...")
                print(f"Expected SHA512 (str): {expected_sha512_str[:50]}...")
                print(f"Expected SHA256 (str): {expected_sha256_str[:50]}...")
                print(f"Expected SHA512 (bytes): {expected_sha512_bytes[:50]}...")
                print(f"Expected SHA256 (bytes): {expected_sha256_bytes[:50]}...")
                
                if signature in [expected_sha512_str, expected_sha256_str, expected_sha512_bytes, expected_sha256_bytes]:
                    auth_valid = True
                    print("✅ Raw signature verified!")
        
        if not auth_valid and secure_token:
            # Fallback: secure-token header (V1 style)
            if secure_token == secret:
                auth_valid = True
                print("✅ Secure-token verified (fallback)!")
            else:
                print(f"❌ Secure-token mismatch!")
        
        # DEV MODE: Accept any x-casso-signature for testing
        if not auth_valid and DEV_BYPASS_SIGNATURE and signature_header:
            auth_valid = True
            print("⚠️ DEV BYPASS: Accepting webhook (signature present but not verified)")
        
        if not auth_valid:
            print(f"❌ No valid authentication! Rejecting webhook.")
            raise HTTPException(status_code=401, detail="Missing or invalid authentication")
        
        # Parse body
        data = json.loads(body_str)
        print(f"📩 Webhook data: {json.dumps(data)[:500]}...")
        
        # Handle both array and single object format
        raw_data = data.get("data", [])
        if isinstance(raw_data, dict):
            # Single object (test/V2 format)
            transactions = [raw_data]
        elif isinstance(raw_data, list):
            # Array (production format)
            transactions = raw_data
        else:
            transactions = []
        
        if not transactions: return {"success":True,"message":"No transactions"}
        for t in transactions:
            amount = int(t.get("amount", 0))
            desc = t.get("description", "").upper()
            tid = t.get("tid", "")
            
            # FIX #2: Robust trans_code extraction with regex
            trans_code = None
            match = re.search(r'AFK[A-Z0-9]+', desc)
            if match:
                trans_code = match.group(0)
            else:
                # Fallback: try original split method
                if "AFK" in desc:
                    parts = desc.split()
                    for part in parts:
                        if part.startswith("AFK"):
                            trans_code = re.sub(r'[^A-Z0-9]', '', part)  # Strip non-alnum
                            break
            
            if not trans_code:
                print(f"⚠️ No trans_code found in: {desc}")
                continue
            
            # Find order
            order = db.execute(text("SELECT * FROM bank_orders WHERE trans_code=:code AND status='pending'"), {"code": trans_code}).fetchone()
            
            if not order:
                print(f"⚠️ Order not found or already completed: {trans_code}")
                continue
            
            # FIX #3: Amount tolerance (allow 1000 VND variance)
            order_amount = order[5]
            if abs(amount - order_amount) > 1000:
                print(f"⚠️ Amount mismatch: expected {order_amount}, got {amount} (diff={abs(amount-order_amount)})")
                continue
            
            # Generate license
            license_key = f"AFK-{secrets.token_hex(16).upper()}"
            tier = order[3]
            duration_days = order[4]
            device_id = order[2]  # order[0]=id, [1]=trans_code, [2]=device_id
            
            # Create license in licenses table
            expires_at = datetime.now() + timedelta(days=duration_days)
            max_devices = get_max_devices_for_tier(tier)  # basic=2, pro=5, enterprise=-1
            
            result = db.execute(text("""
                INSERT INTO licenses (license_key, tier, duration_days, max_devices, expires_at, is_active, created_at)
                VALUES (:key, :tier, :days, :max, :exp, TRUE, NOW())
                RETURNING id
            """), {"key": license_key, "tier": tier, "days": duration_days, "max": max_devices, "exp": expires_at})
            
            license_id = result.fetchone()[0]
            
            # Activate license for device
            db.execute(text("""
                INSERT INTO license_devices (license_key, device_id, activated_at)
                VALUES (:key, :did, NOW())
            """), {"key": license_key, "did": device_id})
            
            # Update order status
            db.execute(text("""
                UPDATE bank_orders 
                SET status='success', license_key=:key, paid_at=NOW(), bank_tid=:tid
                WHERE trans_code=:code
            """), {"key": license_key, "tid": tid, "code": trans_code})
            
            db.commit()
            print(f"✅ Webhook completed order {trans_code}: License {license_key} for device {device_id[:20]}...")
        return {"success":True,"return_code":1}
    except HTTPException:
        raise
    except Exception as e: print(f"❌ Error: {e}"); return {"success":1,"return_code":1,"error":str(e)}

@app.get("/payment/bank/status")
def bank_status(trans_code: str, db: Session = Depends(get_db)):
    order = db.execute(text("SELECT * FROM bank_orders WHERE trans_code=:code"),{"code":trans_code}).fetchone()
    if not order: raise HTTPException(404,"Order not found")
    return {"trans_code":trans_code,"status":order[8],"amount":order[5],"tier":order[3],"duration_days":order[4],"license_key":order[9] if order[8]=="success" else None,"created_at":to_iso(order[11]),"paid_at":to_iso(order[12])}
# AFK Zone Admin Backend - FULL IMPLEMENTATION
# Add to existing app.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text, desc
from typing import Optional, List
import hashlib
import secrets
import hmac
import jwt
import bcrypt
from database import get_db

# ==================== ADMIN AUTH ====================

SECRET_KEY = JWT_SECRET
ALGORITHM = "HS256"
security = HTTPBearer()

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminUser(BaseModel):
    username: str
    role: str

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=24)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        # Handle both PyJWT 1.x and 2.x error types
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/admin/login")
def admin_login(req: AdminLoginRequest, request: Request, db: Session = Depends(get_db)):
    """Admin login - returns JWT token with lockout protection"""
    from security_lockout import (
        check_lockout, get_lockout_remaining, record_failed_login,
        clear_failed_logins, log_successful_login
    )
    import logging
    security_logger = logging.getLogger("admin_security")
    
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Check lockout BEFORE password verify
    if check_lockout(client_ip):
        remaining = get_lockout_remaining(client_ip)
        security_logger.warning(f"Blocked login attempt from locked IP: ip={client_ip} remaining={remaining}s")
        raise HTTPException(
            status_code=429,
            detail=f"Account temporarily locked. Try again in {remaining} seconds."
        )
    
    result = db.execute(
        text("SELECT * FROM admin_users WHERE username=:username"),
        {"username": req.username}
    ).fetchone()

    if not result:
        # Record failed attempt (username not found)
        record_failed_login(client_ip, req.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Check password (bcrypt)
    if not bcrypt.checkpw(req.password.encode(), result[2].encode()):
        # Record failed attempt (wrong password)
        record_failed_login(client_ip, req.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Login successful - clear failed attempts and log
    clear_failed_logins(client_ip)
    log_successful_login(client_ip, result[1])

    # Create JWT token
    access_token = create_access_token(
        data={"sub": result[1], "role": result[3]}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": result[1],
        "role": result[3],
        "expires_in": 86400
    }

# ==================== PRODUCTS MANAGEMENT ====================
@app.get("/admin/licenses")
def list_licenses_admin(
    page: int = 1,
    limit: int = 100,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: List all licenses with JWT auth"""
    offset = (page - 1) * limit
    results = db.execute(text("""
        SELECT * FROM licenses 
        ORDER BY created_at DESC 
        LIMIT :limit OFFSET :offset
    """), {"limit": limit, "offset": offset}).fetchall()
    
    total = db.execute(text("SELECT COUNT(*) FROM licenses")).scalar()
    
    licenses = []
    for r in results:
        licenses.append({
            "license_key": r[1] if len(r) > 1 else None,
            "tier": r[2] if len(r) > 2 else None,
            "duration_days": r[3] if len(r) > 3 else None,
            "activated_at": to_iso(r[4]) if len(r) > 4 else None,
            "expires_at": to_iso(r[5]) if len(r) > 5 else None,
            "device_id": r[6] if len(r) > 6 else None,
            "max_devices": r[7] if len(r) > 7 else None,
            "is_revoked": r[9] if len(r) > 9 else False,
            "is_trial": r[11] if len(r) > 11 else False
        })
    
    return {"total": total or 0, "licenses": licenses}

@app.post("/admin/orders/{trans_code}/complete")
def manual_complete_order(
    trans_code: str,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Manually complete a bank order"""
    import secrets
    from datetime import datetime, timedelta
    
    # Get order
    order = db.execute(text("SELECT * FROM bank_orders WHERE trans_code=:code"), {"code": trans_code}).fetchone()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order[8] == 'success':  # status column
        return {"success": False, "message": "Order already completed", "license_key": order[9]}
    
    trans_code_db, device_id, tier, duration_days, amount = order[1], order[2], order[3], order[4], order[5]  # order[0]=id, [1]=trans_code, [2]=device_id
    
    # Generate license key
    license_key = f"AFK-{secrets.token_hex(16).upper()}"
    
    # Create license with device_id (old schema)
    expires_at = datetime.now() + timedelta(days=duration_days)
    
    # Get max_devices for tier
    max_devices = get_max_devices_for_tier(tier)
    
    db.execute(text("""
        INSERT INTO licenses (license_key, tier, duration_days, max_devices, activated_at, expires_at, is_active, created_at)
        VALUES (:key, :tier, :dur, :max, NOW(), :exp, TRUE, NOW())
    """), {"key": license_key, "tier": tier, "dur": duration_days, "max": max_devices, "exp": expires_at})
    
    # Add device to license_devices
    db.execute(text("""
        INSERT INTO license_devices (license_key, device_id, activated_at)
        VALUES (:key, :dev, NOW())
    """), {"key": license_key, "dev": device_id})
    
    # Update order status
    db.execute(text("""
        UPDATE bank_orders 
        SET status='success', license_key=:key, paid_at=NOW()
        WHERE trans_code=:code
    """), {"key": license_key, "code": trans_code})
    
    db.commit()
    
    return {
        "success": True,
        "message": "Order completed successfully",
        "license_key": license_key,
        "tier": tier,
        "duration_days": duration_days
    }

@app.get("/admin/orders")
def get_all_orders(
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    limit: int = 50
):
    """Admin: Get all bank orders"""
    query = "SELECT * FROM bank_orders"
    params = {}
    
    if status:
        query += " WHERE status=:status"
        params["status"] = status
    
    query += " ORDER BY created_at DESC LIMIT :limit"
    params["limit"] = limit
    
    orders = db.execute(text(query), params).fetchall()
    
    return {
        "orders": [
            {
                "id": o[0],
                "trans_code": o[1],
                "device_id": o[2],
                "tier": o[3],
                "duration_days": o[4],
                "amount": o[5],
                "status": o[8],
                "license_key": o[9],
                "created_at": to_iso(o[11]),
                "paid_at": to_iso(o[12])
            }
            for o in orders
        ]
    }



@app.delete("/admin/devices/{device_id}")
def delete_device(
    device_id: str,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Remove device from license"""
    db.execute(text("DELETE FROM license_devices WHERE device_id=:device_id"), {"device_id": device_id})
    db.commit()
    return {"success": True, "message": f"Device {device_id} removed successfully"}
@app.get("/admin/connections")
def get_connections(
    page: int = 1,
    limit: int = 100,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Get connection logs"""
    offset = (page - 1) * limit
    
    try:
        results = db.execute(text("""
            SELECT device_id, peer_id, connection_type, ip_address, connected_at, disconnected_at, duration_seconds, license_key
            FROM connection_logs
            ORDER BY connected_at DESC
            LIMIT :limit OFFSET :offset
        """), {"limit": limit, "offset": offset}).fetchall()
        
        total = db.execute(text("SELECT COUNT(*) FROM connection_logs")).scalar() or 0
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "connections": [
                {
                    "device_id": r[0],
                    "peer_id": r[1],
                    "connection_type": r[2],
                    "ip_address": r[3],
                    "connected_at": to_iso(r[4]),
                    "disconnected_at": to_iso(r[5]),
                    "duration_seconds": r[6],
                    "license_key": r[7]
                } for r in results
            ]
        }
    except Exception:
        # Table doesn't exist
        return {"total": 0, "page": page, "limit": limit, "connections": []}

class SingleLicenseRequest(BaseModel):
    tier: str
    duration_days: int
    max_devices: Optional[int] = None
    notes: Optional[str] = None

@app.post("/admin/licenses/generate")
def generate_single_license(
    req: SingleLicenseRequest,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Generate a single license"""
    key = f"AFK-{req.tier.upper()}-{secrets.token_hex(12).upper()}"
    
    db.execute(text("""
        INSERT INTO licenses (license_key, tier, duration_days, max_devices, created_by, notes)
        VALUES (:key, :tier, :days, :devices, 'admin', :note)
    """), {
        "key": key,
        "tier": req.tier,
        "days": req.duration_days,
        "devices": req.max_devices or 1,
        "note": req.notes
    })
    
    db.commit()
    
    return {
        "success": True,
        "license_key": key,
        "tier": req.tier,
        "duration_days": req.duration_days,
        "max_devices": req.max_devices
    }






class ProductCreate(BaseModel):
    name: str
    tier: str  # basic, pro, enterprise
    duration_days: int
    price: int
    max_devices: int
    is_active: bool = True
    display_order: int = 0
    description: Optional[str] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    tier: Optional[str] = None
    duration_days: Optional[int] = None
    price: Optional[int] = None
    max_devices: Optional[int] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    description: Optional[str] = None

@app.get("/products")
def get_products(active_only: bool = True, db: Session = Depends(get_db)):
    """Get all products with formatted display fields"""
    query = "SELECT * FROM products WHERE is_active=TRUE ORDER BY display_order, id" if active_only else "SELECT * FROM products ORDER BY display_order, id"
    results = db.execute(text(query)).fetchall()

    products = []
    for r in results:
        price, max_dev = r[4], r[5]

        # Format display_price
        if price == 0:
            display_price = "Miễn phí"
        elif price >= 1000:
            display_price = f"{price // 1000}.000đ"
        else:
            display_price = f"{price}đ"

        # Format max_devices_display
        if max_dev == -1:
            max_devices_display = "Vô cực"
        else:
            max_devices_display = f"{max_dev} thiết bị"

        products.append({
            "id": r[0],
            "name": r[1],
            "tier": r[2],
            "duration_days": r[3],
            "price": r[4],
            "display_price": display_price,  # NEW!
            "max_devices": r[5],
            "max_devices_display": max_devices_display,  # NEW!
            "is_active": r[6],
            "display_order": r[7],
            "description": r[8]
        })

    return {"products": products}

@app.post("/admin/products")
def create_product(product: ProductCreate, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Create new product"""
    db.execute(text("""
        INSERT INTO products (name, tier, duration_days, price, max_devices, is_active, display_order, description)
        VALUES (:name, :tier, :days, :price, :devices, :active, :order, :desc)
    """), {
        "name": product.name,
        "tier": product.tier,
        "days": product.duration_days,
        "price": product.price,
        "devices": product.max_devices,
        "active": product.is_active,
        "order": product.display_order,
        "desc": product.description
    })
    db.commit()
    return {"success": True, "message": "Product created successfully"}

@app.put("/admin/products/{product_id}")
def update_product(product_id: int, product: ProductUpdate, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Update product"""
    updates = []
    params = {"id": product_id}

    if product.name:
        updates.append("name=:name")
        params["name"] = product.name
    if product.tier is not None:
        updates.append("tier=:tier")
        params["tier"] = product.tier
    if product.duration_days is not None:
        updates.append("duration_days=:days")
        params["days"] = product.duration_days
    if product.price is not None:
        updates.append("price=:price")
        params["price"] = product.price
    if product.max_devices is not None:
        updates.append("max_devices=:devices")
        params["devices"] = product.max_devices
    if product.is_active is not None:
        updates.append("is_active=:active")
        params["active"] = product.is_active
    if product.display_order is not None:
        updates.append("display_order=:order")
        params["order"] = product.display_order
    if product.description is not None:
        updates.append("description=:desc")
        params["desc"] = product.description

    if updates:
        db.execute(text(f"UPDATE products SET {', '.join(updates)} WHERE id=:id"), params)
        db.commit()

    return {"success": True, "message": "Product updated successfully"}

@app.delete("/admin/products/{product_id}")
def delete_product(product_id: int, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Delete product (soft delete)"""
    db.execute(text("UPDATE products SET is_active=FALSE WHERE id=:id"), {"id": product_id})
    db.commit()
    return {"success": True, "message": "Product deleted successfully"}

@app.delete("/admin/products/{product_id}/permanent")
def delete_product_permanent(
    product_id: int,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Permanently delete a product"""
    # Check if product exists
    product = db.execute(text("SELECT * FROM products WHERE id=:id"), {"id": product_id}).fetchone()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Delete from pricing table
    db.execute(text("DELETE FROM pricing WHERE tier=:tier AND duration_days=:days"), 
               {"tier": product[2], "days": product[3]})
    
    # Delete product
    db.execute(text("DELETE FROM products WHERE id=:id"), {"id": product_id})
    db.commit()
    
    return {"success": True, "message": "Product permanently deleted"}




# ==================== ENABLE PRODUCT ====================
@app.post("/admin/products/{product_id}/enable")
def enable_product(product_id: int, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Enable product (set is_active=TRUE)"""
    # Check if product exists
    product = db.execute(text("SELECT * FROM products WHERE id=:id"), {"id": product_id}).fetchone()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.execute(text("UPDATE products SET is_active=TRUE WHERE id=:id"), {"id": product_id})
    db.commit()
    return {"success": True, "message": "Product enabled successfully"}

# ==================== DISABLE PRODUCT ====================
@app.post("/admin/products/{product_id}/disable")
def disable_product(product_id: int, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Disable product (set is_active=FALSE)"""
    product = db.execute(text("SELECT * FROM products WHERE id=:id"), {"id": product_id}).fetchone()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.execute(text("UPDATE products SET is_active=FALSE WHERE id=:id"), {"id": product_id})
    db.commit()
    return {"success": True, "message": "Product disabled successfully"}

# ==================== DASHBOARD STATS ====================

@app.get("/admin/dashboard/stats")
def get_dashboard_stats(token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Get dashboard overview stats"""

    # Total devices (with error handling)
    try:
        total_devices = db.execute(text("SELECT COUNT(*) FROM devices")).scalar() or 0
    except Exception:
        total_devices = 0

    # Active devices (last 24h)
    try:
        active_24h = db.execute(text(
            "SELECT COUNT(*) FROM devices WHERE last_seen > NOW() - INTERVAL '24 hours'"
        )).scalar() or 0
    except Exception:
        active_24h = 0

    # Active licenses (with error handling)
    try:
        active_licenses = db.execute(text(
            "SELECT COUNT(*) FROM licenses WHERE expires_at > NOW() AND activated_at IS NOT NULL"
        )).scalar() or 0
    except Exception:
        active_licenses = 0

    # Expired licenses
    try:
        expired_licenses = db.execute(text(
            "SELECT COUNT(*) FROM licenses WHERE expires_at <= NOW() AND activated_at IS NOT NULL"
        )).scalar() or 0
    except Exception:
        expired_licenses = 0

    # Revenue (with error handling for missing payments table)
    try:
        revenue_today = db.execute(text(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='success' AND DATE(completed_at) = CURRENT_DATE"
        )).scalar() or 0
    except Exception:
        revenue_today = 0

    try:
        revenue_month = db.execute(text(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='success' AND EXTRACT(MONTH FROM completed_at) = EXTRACT(MONTH FROM NOW())"
        )).scalar() or 0
    except Exception:
        revenue_month = 0

    try:
        revenue_all = db.execute(text(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status='success'"
        )).scalar() or 0
    except Exception:
        revenue_all = 0

    # Server stats (if exists)
    try:
        server_stats = db.execute(text(
            "SELECT cpu_usage_percent, memory_usage_mb, active_connections, bandwidth_in_mbps, bandwidth_out_mbps FROM server_stats ORDER BY timestamp DESC LIMIT 1"
        )).fetchone()
    except Exception:
        server_stats = None

    return {
        "total_devices": total_devices or 0,
        "active_devices_24h": active_24h or 0,
        "total_licenses_active": active_licenses or 0,
        "total_licenses_expired": expired_licenses or 0,
        "total_revenue_today": revenue_today,
        "total_revenue_month": revenue_month,
        "total_revenue_all": revenue_all,
        "server_status": {
            "cpu_usage": server_stats[0] if server_stats else 0,
            "memory_usage_mb": server_stats[1] if server_stats else 0,
            "active_connections": server_stats[2] if server_stats else 0,
            "bandwidth_in_mbps": server_stats[3] if server_stats else 0,
            "bandwidth_out_mbps": server_stats[4] if server_stats else 0
        } if server_stats else None
    }

# ==================== USER MANAGEMENT ====================

@app.get("/admin/users")
def get_users(
    page: int = 1,
    limit: int = 50,
    status: Optional[str] = None,
    tier: Optional[str] = None,
    search: Optional[str] = None,
    token: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Admin: Get all users with pagination"""
    offset = (page - 1) * limit
    where_clauses = []
    params = {"limit": limit, "offset": offset}

    if status:
        where_clauses.append("license_status=:status")
        params["status"] = status

    if tier:
        where_clauses.append("license_tier=:tier")
        params["tier"] = tier

    if search:
        where_clauses.append("(device_id ILIKE :search OR device_model ILIKE :search)")
        params["search"] = f"%{search}%"

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Get total count
    total = db.execute(text(f"SELECT COUNT(*) FROM devices WHERE {where_sql}"), params).scalar()

    # Get users
    results = db.execute(text(f"""
        SELECT * FROM devices
        WHERE {where_sql}
        ORDER BY last_seen DESC
        LIMIT :limit OFFSET :offset
    """), params).fetchall()

    return {
        "total": total or 0,
        "page": page,
        "limit": limit,
        "users": [
            {
                "device_id": r[1],
                "device_fingerprint": r[2],
                "device_model": r[3],
                "os_version": r[4],
                "app_version": r[5],
                "first_seen": to_iso(r[6]),
                "last_seen": to_iso(r[7]),
                "last_ip": r[8],
                "license_key": r[9],
                "license_status": r[10],
                "license_tier": r[11],
                "license_expires_at": to_iso(r[12]),
                "is_active": r[13],
                "total_sessions": r[14]
            } for r in results
        ]
    }

# ==================== LICENSE MANAGEMENT ====================

class BulkLicenseCreate(BaseModel):
    tier: str
    duration_days: int
    count: int  # 1-100
    max_devices: int = 1
    note: Optional[str] = None

class LicenseAirdrop(BaseModel):
    device_ids: List[str]
    tier: str
    duration_days: int
    note: Optional[str] = None

@app.post("/admin/licenses/bulk-create")
def bulk_create_licenses(req: BulkLicenseCreate, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Bulk create licenses"""
    if req.count < 1 or req.count > 100:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 100")

    license_keys = []
    for _ in range(req.count):
        key = f"AFK-{req.tier.upper()}-{secrets.token_hex(12).upper()}"
        expires_dt = datetime.now() + timedelta(days=req.duration_days)

        db.execute(text("""
            INSERT INTO licenses (license_key, tier, duration_days, expires_at, max_devices, created_by, notes)
            VALUES (:key, :tier, :days, :exp, :devices, 'admin', :note)
        """), {
            "key": key,
            "tier": req.tier,
            "days": req.duration_days,
            "exp": expires_dt,
            "devices": req.max_devices,
            "note": req.note
        })

        license_keys.append(key)

    db.commit()

    return {
        "success": True,
        "created": len(license_keys),
        "license_keys": license_keys
    }

@app.post("/admin/licenses/airdrop")
def airdrop_licenses(req: LicenseAirdrop, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Airdrop licenses to specific devices"""
    licenses_created = []

    for device_id in req.device_ids:
        key = f"AFK-{req.tier.upper()}-{secrets.token_hex(12).upper()}"
        now = datetime.now()
        expires_dt = now + timedelta(days=req.duration_days)

        # Create license
        db.execute(text("""
            INSERT INTO licenses (license_key, tier, duration_days, expires_at, device_id, activated_at, created_by, notes)
            VALUES (:key, :tier, :days, :exp, :dev, :now, 'admin_airdrop', :note)
        """), {
            "key": key,
            "tier": req.tier,
            "days": req.duration_days,
            "exp": expires_dt,
            "dev": device_id,
            "now": now,
            "note": req.note
        })

        # Update device (devices.license_expires_at is bigint, need epoch ms)
        expires_epoch_ms = int(expires_dt.timestamp() * 1000)
        db.execute(text("""
            UPDATE devices
            SET license_key=:key, license_status='active', license_tier=:tier, license_expires_at=:exp
            WHERE device_id=:dev
        """), {
            "key": key,
            "tier": req.tier,
            "exp": expires_epoch_ms,
            "dev": device_id
        })

        licenses_created.append({"device_id": device_id, "license_key": key})

    db.commit()

    return {
        "success": True,
        "licenses_created": len(licenses_created),
        "devices_notified": len(req.device_ids),
        "licenses": licenses_created
    }

# @app.post("/admin/licenses/{license_key}/revoke") # DISABLED - old version
# def revoke_license(license_key: str, reason: str, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
#     """Admin: Revoke a license"""
#     db.execute(text("""
#         UPDATE licenses
#         SET is_revoked=TRUE, revoked_at=NOW(), revoked_reason=:reason
#         WHERE license_key=:key
#     """), {"key": license_key, "reason": reason})
# 
#     db.commit()
# 
#     return {
#         "success": True,
#         "license_key": license_key,
#         "revoked_at": datetime.now().isoformat()
#     }

# ==================== DEVICE HEARTBEAT ====================

class HeartbeatRequest(BaseModel):
    device_id: str
    app_version: str
    license_status: Optional[str] = None

@app.post("/heartbeat")
def device_heartbeat(req: HeartbeatRequest, db: Session = Depends(get_db)):
    """Device sends heartbeat every hour"""
    # Update or create device
    db.execute(text("""
        INSERT INTO devices (device_id, app_version, last_seen, total_sessions)
        VALUES (:dev, :ver, NOW(), 1)
        ON CONFLICT (device_id)
        DO UPDATE SET app_version=:ver, last_seen=NOW(), total_sessions=devices.total_sessions+1
    """), {"dev": req.device_id, "ver": req.app_version})

    # Record heartbeat
    db.execute(text("""
        INSERT INTO device_heartbeats (device_id, app_version, license_status)
        VALUES (:dev, :ver, :status)
    """), {"dev": req.device_id, "ver": req.app_version, "status": req.license_status})

    db.commit()

    return {"success": True, "message": "Heartbeat received"}

# ==================== ANALYTICS ====================

@app.get("/admin/analytics/revenue")
def get_revenue_analytics(period: str = "30d", token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Get revenue analytics"""
    if period == "30d":
        interval = "30 days"
    elif period == "90d":
        interval = "90 days"
    else:
        interval = "30 days"

    # Total revenue
    total = db.execute(text(f"""
        SELECT COALESCE(SUM(amount), 0)
        FROM payments
        WHERE status='success' AND completed_at > NOW() - INTERVAL '{interval}'
    """)).scalar() or 0

    # Daily revenue
    daily = db.execute(text(f"""
        SELECT DATE(completed_at) as date, SUM(amount) as total
        FROM payments
        WHERE status='success' AND completed_at > NOW() - INTERVAL '{interval}'
        GROUP BY DATE(completed_at)
        ORDER BY date
    """)).fetchall()

    # By tier
    by_tier = db.execute(text(f"""
        SELECT tier, SUM(amount) as total
        FROM payments
        WHERE status='success' AND completed_at > NOW() - INTERVAL '{interval}'
        GROUP BY tier
    """)).fetchall()

    return {
        "total_revenue": total,
        "daily_revenue": [{"date": r[0].isoformat(), "amount": int(r[1])} for r in daily],
        "by_tier": {r[0]: int(r[1]) for r in by_tier}
    }
# Add to app.py - License Extend & User Renew

# 1. ADMIN EXTEND - Fixed logic (extend from expires_at, not now)
@app.put("/admin/licenses/{license_key}/extend")
def admin_extend_license(license_key: str, additional_days: int, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Extend license expiry - ALWAYS from current expires_at"""
    result = db.execute(text(
        "SELECT expires_at, duration_days FROM licenses WHERE license_key=:key"
    ), {"key": license_key}).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="License not found")

    # Use to_datetime for proper parsing
    current_exp = to_datetime(result[0])
    if not current_exp:
        raise HTTPException(status_code=500, detail="Invalid expires_at in database")
    
    new_exp = current_exp + timedelta(days=additional_days)

    db.execute(text(
        "UPDATE licenses SET expires_at=:exp, duration_days=:total_days WHERE license_key=:key"
    ), {
        "exp": new_exp,
        "total_days": (result[1] or 0) + additional_days,
        "key": license_key
    })

    db.commit()

    return {
        "success": True,
        "old_expires_at": to_iso(current_exp),
        "new_expires_at": to_iso(new_exp),
        "extended_days": additional_days,
        "message": f"License extended by {additional_days} days"
    }

# 2. USER SELF-RENEW - Purchase extension (same tier)
class UserRenewRequest(BaseModel):
    license_key: str
    device_id: str
    product_id: int  # From products table

@app.post("/user/license/renew")
def user_renew_license(req: UserRenewRequest, db: Session = Depends(get_db)):
    """User: Buy extension for existing license (create payment order)"""

    # Verify license ownership
    license_result = db.execute(text(
        "SELECT tier, expires_at FROM licenses WHERE license_key=:key AND device_id=:dev"
    ), {"key": req.license_key, "dev": req.device_id}).fetchone()

    if not license_result:
        raise HTTPException(status_code=403, detail="License not found or not yours")

    # Get product info
    product = db.execute(text(
        "SELECT * FROM products WHERE id=:id AND is_active=TRUE"
    ), {"id": req.product_id}).fetchone()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Verify same tier
    if product[2] != license_result[0]:  # tier column
        raise HTTPException(status_code=400, detail=f"Product must be same tier ({license_result[0]})")

    # Create payment order (will extend on payment success)
    trans_code = f"RENEW-{secrets.token_hex(8).upper()}"
    content = f"AFKZONE RENEW {trans_code}"

    # Casso QR code
    qr_url = f"https://img.vietqr.io/image/970422-0823333374-compact2.jpg?amount={product[4]}&addInfo={content}"

    db.execute(text("""
        INSERT INTO payments (trans_code, device_id, tier, duration_days, amount, status, license_key, payment_type)
        VALUES (:code, :dev, :tier, :days, :amount, 'pending', :key, 'renew')
    """), {
        "code": trans_code,
        "dev": req.device_id,
        "tier": product[2],
        "days": product[3],
        "amount": product[4],
        "key": req.license_key
    })

    db.commit()

    current_exp_value = license_result[1]
    if isinstance(current_exp_value, datetime):
        current_exp_dt = current_exp_value
    elif isinstance(current_exp_value, (int, float)):
        current_exp_dt = datetime.fromtimestamp(current_exp_value / 1000)
    else:
        try:
            current_exp_dt = datetime.fromisoformat(str(current_exp_value))
        except ValueError:
            current_exp_dt = datetime.now()

    will_extend_to = (current_exp_dt + timedelta(days=product[3])).isoformat()

    return {
        "success": True,
        "trans_code": trans_code,
        "qr_url": qr_url,
        "amount": product[4],
        "bank_info": {
            "bank": "MB Bank",
            "account_no": "0823333374",
            "account_name": "NGUYEN VAN A",
            "content": content
        },
        "product": {
            "name": product[1],
            "duration_days": product[3],
            "will_extend_to": will_extend_to
        }
    }

# 3. UPDATE PAYMENT WEBHOOK - Handle RENEW payments
# Add to existing webhook handler after line where license is created:

# if payment_type == 'renew', extend existing license instead of creating new
@app.post("/webhook/casso")
@app.get("/webhook/casso")  # Allow GET for testing
async def casso_webhook_handler(request: Request, db: Session = Depends(get_db)):
    """Casso webhook - handle payment notifications from bank transfer"""
    import logging
    logging.info("=== CASSO WEBHOOK RECEIVED ===")
    
    try:
        if request.method == "GET":
            return {"status": "webhook active", "message": "Use POST to send payment data"}
        
        # Verify Signature
        signature = request.headers.get("secure-token")
        if not signature:
            logging.warning("Webhook missing secure-token header")
            raise HTTPException(status_code=401, detail="Missing signature")
        
        if signature != CASSO_WEBHOOK_TOKEN:
            logging.warning(f"Invalid webhook signature: {signature}")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        body = await request.json()
        logging.info(f"Webhook body: {body}")
        
        # Casso sends data in 'data' array
        transactions = body.get("data", [body])  # Handle both formats
        
        results = []
        for txn in transactions:
            description = txn.get("description", "")
            amount = txn.get("amount", 0)
            
            logging.info(f"Processing: description={description}, amount={amount}")
            
            # Extract order_id from description (format: AFKZONE_xxx or just search for order_id pattern)
            order_id = None
            
            # Try different patterns
            import re
            # Pattern 1: AFKZONE_xxx
            match = re.search(r'AFKZONE[_\s]*(\w+)', description, re.IGNORECASE)
            if match:
                order_id = f"AFKZONE_{match.group(1)}"
            
            # Pattern 2: Any alphanumeric code
            if not order_id:
                match = re.search(r'([A-Z0-9]{8,})', description)
                if match:
                    order_id = match.group(1)
            
            if not order_id:
                results.append({"error": "Order ID not found in description", "description": description})
                continue
            
            logging.info(f"Found order_id: {order_id}")
            
            # Find order in database
            order = db.execute(text(
                "SELECT * FROM orders WHERE order_id=:oid AND payment_status='pending'"
            ), {"oid": order_id}).fetchone()
            
            if not order:
                # Try partial match
                order = db.execute(text(
                    "SELECT * FROM orders WHERE order_id LIKE :oid AND payment_status='pending'"
                ), {"oid": f"%{order_id}%"}).fetchone()
            
            if not order:
                results.append({"error": "Order not found or already processed", "order_id": order_id})
                continue
            
            # order columns: id, order_id, device_id, device_fingerprint, tier, duration_days, amount, ...
            order_amount = order[6]  # amount column
            device_id = order[2]
            tier = order[4]
            duration_days = order[5]
            
            # Check amount (allow some tolerance for fees)
            if abs(amount - order_amount) > 1000:  # Allow 1000 VND tolerance
                results.append({"error": f"Amount mismatch: got {amount}, expected {order_amount}", "order_id": order_id})
                continue
            
            # Generate license key
            import secrets
            license_key = f"AFK-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
            
            # Calculate expiry
            from datetime import datetime, timedelta
            expires_at_dt = datetime.now() + timedelta(days=duration_days)
            expires_at_ms = int(expires_at_dt.timestamp() * 1000)
            expires_at_iso = expires_at_dt.isoformat()
            
            # Create license
            db.execute(text("""
                INSERT INTO licenses (license_key, tier, max_devices, expires_at, is_active, created_at)
                VALUES (:key, :tier, 2, :exp, TRUE, NOW())
            """), {"key": license_key, "tier": tier, "exp": expires_at_ms})
            
            # Update order
            db.execute(text("""
                UPDATE orders SET payment_status='success', paid_at=NOW(), license_key=:key
                WHERE order_id=:oid
            """), {"key": license_key, "oid": order_id})
            
            db.commit()
            
            logging.info(f"License created: {license_key} for order {order_id}")
            
            # Notify WebSocket clients
            try:
                import asyncio
                asyncio.create_task(payment_manager.notify_payment_complete(order_id, license_key, expires_at_iso))
            except Exception as ws_err:
                logging.warning(f"Could not notify WebSocket: {ws_err}")
            
            results.append({
                "success": True,
                "order_id": order_id,
                "license_key": license_key,
                "expires_at": expires_at_iso
            })
        
        return {"success": True, "results": results}
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logging.error(f"Webhook error: {e}")
        logging.error(traceback.format_exc())
        return {"success": False, "error": str(e)}
        print(f"Error getting connections: {e}")
        return {"connections": []}

# ==================== LICENSE MANAGEMENT ====================

@app.delete("/admin/licenses/{license_key}")
async def delete_license(license_key: str, token: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Permanently delete a license"""
    try:
        # First delete from license_devices
        db.execute(text("DELETE FROM license_devices WHERE license_key = :key"), {"key": license_key})
        # Then delete the license
        result = db.execute(text("DELETE FROM licenses WHERE license_key = :key"), {"key": license_key})
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="License not found")
        
        return {"message": "License deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/licenses/{license_key}/revoke")
async def revoke_license_v2(license_key: str, token: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Revoke a license - will block client on next check"""
    try:
        result = db.execute(text("""
            UPDATE licenses 
            SET is_revoked = true, revoked_at = NOW(), revoked_reason = 'Admin revoked'
            WHERE license_key = :key
        """), {"key": license_key})
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="License not found")
        
        return {"message": "License revoked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/licenses/{license_key}/unrevoke")
async def unrevoke_license(license_key: str, token: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Unrevoke a license - restore access"""
    try:
        result = db.execute(text("""
            UPDATE licenses 
            SET is_revoked = false, revoked_at = NULL, revoked_reason = NULL
            WHERE license_key = :key
        """), {"key": license_key})
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="License not found")
        
        return {"message": "License unrevoked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
# ==================== MULTI-DEVICE ACTIVATION FIX ====================
@app.post("/activate-v2")
def activate_license_v2(data: dict, db: Session = Depends(get_db)):
    """Activate license on a device - supports multi-device"""
    license_key = data.get("license_key")
    device_id = data.get("device_id")
    
    if not license_key or not device_id:
        raise HTTPException(status_code=400, detail="Missing license_key or device_id")
    
    # Check if license exists
    lic = db.execute(
        text("SELECT license_key, tier, duration_days, activated_at, expires_at, max_devices, is_revoked FROM licenses WHERE license_key=:key"),
        {"key": license_key}
    ).fetchone()
    
    if not lic:
        raise HTTPException(status_code=404, detail="License không hợp lệ")
    
    if lic[6]:  # is_revoked
        raise HTTPException(status_code=403, detail="License đã bị thu hồi")
    
    max_devices = lic[5] or 1
    
    # Check if device is already activated with this license
    existing = db.execute(
        text("SELECT id FROM license_devices WHERE license_key=:key AND device_id=:device"),
        {"key": license_key, "device": device_id}
    ).fetchone()
    
    if existing:
        # Device already activated - return success
        return {
            "status": "active",
            "tier": lic[1],
            "duration_days": lic[2],
            "expires_at": to_iso(lic[4]),
            "max_devices": max_devices,
            "message": "Device đã được kích hoạt trước đó"
        }
    
    # Count current activated devices
    device_count = db.execute(
        text("SELECT COUNT(*) FROM license_devices WHERE license_key=:key"),
        {"key": license_key}
    ).scalar() or 0
    
    # Check if max devices reached (skip check if max_devices = -1 = unlimited)
    if max_devices != -1 and device_count >= max_devices:
        raise HTTPException(
            status_code=400, 
            detail=f"License đã đạt giới hạn {max_devices} thiết bị. Vui lòng xóa thiết bị cũ hoặc nâng cấp gói."
        )
    
    # Activate on this device
    db.execute(
        text("INSERT INTO license_devices (license_key, device_id, activated_at) VALUES (:key, :device, NOW())"),
        {"key": license_key, "device": device_id}
    )
    
    # Update activated_at if first activation
    if not lic[3]:  # activated_at is NULL
        expires_at = datetime.now() + timedelta(days=lic[2])
        db.execute(
            text("UPDATE licenses SET activated_at=NOW(), expires_at=:exp WHERE license_key=:key"),
            {"key": license_key, "exp": expires_at}
        )
        db.commit()
        return {
            "status": "activated",
            "tier": lic[1],
            "duration_days": lic[2],
            "expires_at": expires_at.isoformat(),
            "max_devices": max_devices,
            "device_count": device_count + 1,
            "message": "Kích hoạt thành công!"
        }
    
    db.commit()
    return {
        "status": "activated",
        "tier": lic[1],
        "duration_days": lic[2],
        "expires_at": to_iso(lic[4]),
        "max_devices": max_devices,
        "device_count": device_count + 1,
        "message": "Thêm thiết bị thành công!"
    }



def admin_notifications_has_target_device_id(db: Session) -> bool:
    try:
        result = db.execute(text("""
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'admin_notifications'
              AND column_name = 'target_device_id'
            LIMIT 1
        """)).fetchone()
        return result is not None
    except Exception:
        db.rollback()
        return False

class NotificationCreate(BaseModel):
    title: str
    message: str
    type: str
    target: str = "all"
    expires_at: Optional[str] = None
    target_device_id: Optional[str] = None

class LogoutRequest(BaseModel):
    license_key: str
    device_id: str

class ConnectionLogRequest(BaseModel):
    device_id: str
    remote_id: Optional[str] = None
    action: Optional[str] = "connect"
    license_key: Optional[str] = None
    ip_address: Optional[str] = None
    peer_id: Optional[str] = None
    connection_type: Optional[str] = None

@app.post("/license/logout")
def logout_device(req: LogoutRequest, db: Session = Depends(get_db)):
    """Remove device from license"""
    try:
        result = db.execute(
            text("DELETE FROM license_devices WHERE license_key=:key AND device_id=:device"),
            {"key": req.license_key, "device": req.device_id}
        )
        db.commit()
        if result.rowcount == 0:
            return {"success": False, "message": "Device not found"}
        return {"success": True, "message": "Device logged out successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/license/info")
def get_license_info(license_key: str, db: Session = Depends(get_db)):
    """Get license info including device count"""
    lic = db.execute(text("""
        SELECT license_key, tier, duration_days, activated_at, expires_at, max_devices, is_revoked
        FROM licenses
        WHERE license_key=:key
    """), {"key": license_key}).fetchone()

    if not lic:
        raise HTTPException(status_code=404, detail="License not found")

    device_count = db.execute(
        text("SELECT COUNT(*) FROM license_devices WHERE license_key=:key"),
        {"key": license_key}
    ).scalar() or 0

    max_devices = lic[5] or 1
    devices_remaining = -1 if max_devices == -1 else max(max_devices - device_count, 0)

    return {
        "license_key": lic[0],
        "tier": lic[1],
        "duration_days": lic[2],
        "activated_at": to_iso(lic[3]),
        "expires_at": to_iso(lic[4]),
        "max_devices": max_devices,
        "device_count": device_count,
        "devices_remaining": devices_remaining,
        "is_revoked": bool(lic[6]) if len(lic) > 6 else False
    }

@app.get("/user/history")
def get_user_history(
    device_id: str, 
    fingerprint: Optional[str] = None, 
    include_trial: bool = False,
    include_expired: bool = False,
    offset: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get purchase history for a device (persistent even after logout)"""
    fingerprint = fingerprint or ""
    
    # Logic:
    # 1. Get Paid licenses from bank_orders (persistent link to device_id)
    # 2. Get Trial/Other licenses where device is owner or currently active
    # 3. Union or distinct combination
    
    # For simplicity and performance, we'll use a UNION ALL approach or a robust OR
    # But to ensuring bank_orders are the primary source, we'll join.
    
    # Query:
    # Select licenses linked via bank_orders OR directly via device_id/fingerprint
    
    sql = """
    SELECT DISTINCT 
        l.license_key, l.tier, l.duration_days, l.expires_at, l.is_revoked, 
        l.created_at, b.trans_code as source, l.max_devices,
        (SELECT COUNT(*) FROM license_devices ld WHERE ld.license_key = l.license_key) as device_count,
        b.paid_at
    FROM licenses l
    LEFT JOIN bank_orders b ON l.license_key = b.license_key
    LEFT JOIN license_devices ld ON l.license_key = ld.license_key
    WHERE 
        (b.device_id = :device_id AND b.status IN ('success', 'completed'))
        OR ld.device_id = :device_id
        OR l.device_id = :device_id
        OR (:fingerprint != '' AND l.device_fingerprint = :fingerprint)
    ORDER BY l.created_at DESC
    LIMIT :limit OFFSET :offset
    """
    
    results = db.execute(text(sql), {
        "device_id": device_id, 
        "fingerprint": fingerprint,
        "limit": limit,
        "offset": offset
    }).fetchall()

    licenses = []
    now = datetime.now()
    
    for row in results:
        license_key = row[0]
        tier = row[1]
        duration = row[2]
        expires_at = to_datetime(row[3])
        is_revoked = row[4]
        created_at = row[5]
        source = row[6]
        max_devices = row[7]
        device_count = row[8]
        paid_at = row[9]
        
        is_expired = expires_at and expires_at < now
        
        # Filter Logic
        if not include_trial and (tier == 'trial' or source == 'trial'):
            continue
        if not include_expired and is_expired:
            continue
            
        # Determine status
        status = "active"
        if is_revoked:
            status = "revoked"
        elif is_expired:
            status = "expired"
            
        # Determine is_trial
        is_trial = (tier == 'trial') or (source == 'trial')
            
        licenses.append({
            "license_key": license_key,
            "tier": tier,
            "duration_days": duration,
            "expires_at": to_iso(expires_at),
            "status": status,
            "paid_at": to_iso(paid_at) if paid_at else None,
            "source": source,
            "device_count": device_count,
            "max_devices": max_devices,
            "created_at": to_iso(created_at),
            "is_trial": is_trial
        })

    return {"licenses": licenses}

@app.post("/license/recover")
def recover_license(data: dict, db: Session = Depends(get_db)):
    """Recover license by transaction code"""
    trans_code = (data.get("trans_code") or "").strip().upper()
    if not trans_code:
        raise HTTPException(status_code=400, detail="Transaction code is required")

    order = db.execute(text("""
        SELECT license_key, status
        FROM bank_orders
        WHERE trans_code = :trans_code
    """), {"trans_code": trans_code}).fetchone()

    if not order:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if order[1] not in ["completed", "success"]:
        raise HTTPException(status_code=400, detail="Transaction not completed")

    license_key = order[0]
    if not license_key:
        raise HTTPException(status_code=400, detail="License not available for this transaction")

    lic = db.execute(text("""
        SELECT license_key, tier, duration_days, expires_at
        FROM licenses
        WHERE license_key = :license_key
    """), {"license_key": license_key}).fetchone()

    if lic:
        return {
            "license_key": lic[0],
            "tier": lic[1],
            "duration_days": lic[2],
            "expires_at": to_iso(lic[3])
        }

    return {"license_key": license_key}

@app.post("/connection/log")
def log_connection(req: ConnectionLogRequest, db: Session = Depends(get_db)):
    """Log a connection from client"""
    try:
        action = (req.action or "connect").lower()
        remote_id = req.remote_id or ""
        peer_id = req.peer_id or remote_id
        connection_type = req.connection_type or "remote"
        ip_address = req.ip_address or ""
        license_key = req.license_key or None

        if action == "disconnect":
            last = db.execute(text("""
                SELECT id, connected_at
                FROM connection_logs
                WHERE device_id = :device_id
                  AND remote_id = :remote_id
                  AND disconnected_at IS NULL
                ORDER BY connected_at DESC
                LIMIT 1
            """), {"device_id": req.device_id, "remote_id": remote_id}).fetchone()

            if last:
                connected_at = to_datetime(last[1])
                duration = int((datetime.now() - connected_at).total_seconds()) if connected_at else 0
                db.execute(text("""
                    UPDATE connection_logs
                    SET disconnected_at = NOW(),
                        duration_seconds = :duration,
                        action = 'disconnect'
                    WHERE id = :id
                """), {"duration": duration, "id": last[0]})
                db.commit()
                return {"status": "logged"}

            db.execute(text("""
                INSERT INTO connection_logs (
                    device_id, remote_id, action, ip_address, connected_at,
                    disconnected_at, duration_seconds, license_key, peer_id, connection_type
                ) VALUES (
                    :device_id, :remote_id, :action, :ip, NOW(),
                    NOW(), 0, :license_key, :peer_id, :connection_type
                )
            """), {
                "device_id": req.device_id,
                "remote_id": remote_id,
                "action": action,
                "ip": ip_address,
                "license_key": license_key,
                "peer_id": peer_id,
                "connection_type": connection_type
            })
            db.commit()
            return {"status": "logged"}

        db.execute(text("""
            INSERT INTO connection_logs (
                device_id, remote_id, action, ip_address, connected_at,
                license_key, peer_id, connection_type
            ) VALUES (
                :device_id, :remote_id, :action, :ip, NOW(),
                :license_key, :peer_id, :connection_type
            )
        """), {
            "device_id": req.device_id,
            "remote_id": remote_id,
            "action": action,
            "ip": ip_address,
            "license_key": license_key,
            "peer_id": peer_id,
            "connection_type": connection_type
        })
        db.commit()
        return {"status": "logged"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "detail": str(e)}

@app.get("/notifications")
def get_user_notifications(device_id: str, db: Session = Depends(get_db)):
    """User: Get all active notifications for this device"""
    device = db.execute(text("""
        SELECT license_status, license_tier, license_expires_at
        FROM devices
        WHERE device_id=:dev
    """), {"dev": device_id}).fetchone()

    license_status = device[0] if device else "none"
    license_expires_at = device[2] if device else None

    has_target_device = admin_notifications_has_target_device_id(db)
    target_clause = "OR target_device_id=:dev" if has_target_device else ""

    results = db.execute(text(f"""
        SELECT id, title, message, type, created_at, expires_at
        FROM admin_notifications
        WHERE is_active=TRUE
          AND (expires_at IS NULL OR expires_at > NOW())
          AND (
              target='all'
              OR target=:status
              {target_clause}
          )
        ORDER BY created_at DESC
        LIMIT 50
    """), {"status": license_status, "dev": device_id}).fetchall()

    notifications = [{
        "id": r[0],
        "title": r[1],
        "message": r[2],
        "type": r[3],
        "created_at": to_iso(r[4]),
        "expires_at": to_iso(r[5]),
        "is_read": False
    } for r in results]

    exp_dt = to_datetime(license_expires_at)
    if exp_dt:
        days_left = (exp_dt - datetime.now()).days
        if 0 < days_left <= 7:
            notifications.insert(0, {
                "id": -1,
                "title": "License expiring soon",
                "message": f"Your license expires in {days_left} day(s). Please renew to avoid interruption.",
                "type": "license_expiry",
                "created_at": datetime.now().isoformat(),
                "expires_at": exp_dt.isoformat(),
                "is_read": False
            })

    return {
        "total": len(notifications),
        "unread": len(notifications),
        "notifications": notifications
    }

@app.post("/admin/notifications")
def create_notification(notif: NotificationCreate, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Create new notification"""
    expires = to_datetime(notif.expires_at)
    has_target_device = admin_notifications_has_target_device_id(db)

    if has_target_device:
        db.execute(text("""
            INSERT INTO admin_notifications (title, message, type, target, expires_at, created_by, target_device_id)
            VALUES (:title, :msg, :type, :target, :exp, :creator, :dev)
        """), {
            "title": notif.title,
            "msg": notif.message,
            "type": notif.type,
            "target": notif.target,
            "exp": expires,
            "creator": token.get("sub"),
            "dev": notif.target_device_id
        })
    else:
        db.execute(text("""
            INSERT INTO admin_notifications (title, message, type, target, expires_at, created_by)
            VALUES (:title, :msg, :type, :target, :exp, :creator)
        """), {
            "title": notif.title,
            "msg": notif.message,
            "type": notif.type,
            "target": notif.target,
            "exp": expires,
            "creator": token.get("sub")
        })

    db.commit()
    return {"success": True, "message": "Notification created"}

@app.get("/admin/notifications")
def get_all_notifications(token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Get all notifications"""
    has_target_device = admin_notifications_has_target_device_id(db)
    columns = "id, title, message, type, target, is_active, created_at, expires_at, created_by"
    if has_target_device:
        columns += ", target_device_id"

    results = db.execute(text(f"""
        SELECT {columns}
        FROM admin_notifications
        ORDER BY created_at DESC
        LIMIT 100
    """)).fetchall()

    notifications = []
    for r in results:
        record = {
            "id": r[0],
            "title": r[1],
            "message": r[2],
            "type": r[3],
            "target": r[4],
            "is_active": r[5],
            "created_at": to_iso(r[6]),
            "expires_at": to_iso(r[7]),
            "created_by": r[8]
        }
        if has_target_device:
            record["target_device_id"] = r[9]
        notifications.append(record)

    return {"notifications": notifications}

@app.delete("/admin/notifications/{notification_id}")
def delete_notification(notification_id: int, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Delete notification"""
    db.execute(text(
        "UPDATE admin_notifications SET is_active=FALSE WHERE id=:id"
    ), {"id": notification_id})
    db.commit()
    return {"success": True, "message": "Notification deleted"}

@app.get("/admin/licenses/all")
def get_all_licenses(token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Get all licenses with device counts"""
    results = db.execute(text("""
        SELECT l.license_key, l.tier, l.duration_days, l.max_devices, l.activated_at, l.expires_at,
               l.created_at, l.is_revoked,
               COALESCE(bo.trans_code, 'manual') as source,
               (SELECT COUNT(*) FROM license_devices ld WHERE ld.license_key = l.license_key) as device_count
        FROM licenses l
        LEFT JOIN bank_orders bo ON bo.license_key = l.license_key
        ORDER BY l.created_at DESC
        LIMIT 100
    """)).fetchall()

    licenses = []
    for row in results:
        expires_at_dt = to_datetime(row[5])
        is_expired = expires_at_dt and expires_at_dt < datetime.now()
        status = "revoked" if row[7] else ("expired" if is_expired else "active")
        licenses.append({
            "license_key": row[0],
            "tier": row[1],
            "duration_days": row[2],
            "max_devices": row[3],
            "activated_at": to_iso(row[4]),
            "expires_at": to_iso(row[5]),
            "created_at": to_iso(row[6]),
            "status": status,
            "source": row[8],
            "device_count": row[9] or 0
        })

    return {"licenses": licenses}

@app.get("/admin/devices/detailed")
def get_detailed_devices(token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Get devices with detailed info"""
    results = db.execute(text("""
        SELECT ld.device_id, ld.device_model, ld.app_version, ld.license_key,
               ld.activated_at, l.tier, l.expires_at
        FROM license_devices ld
        LEFT JOIN licenses l ON l.license_key = ld.license_key
        ORDER BY ld.activated_at DESC
        LIMIT 100
    """)).fetchall()

    devices = []
    for row in results:
        devices.append({
            "device_id": row[0],
            "model": row[1],
            "app_version": row[2],
            "license_key": row[3],
            "activated_at": to_iso(row[4]),
            "tier": row[5],
            "expires_at": to_iso(row[6])
        })

    return {"devices": devices}

@app.get("/admin/trial-devices")
def get_trial_devices(token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Get all trial devices"""
    results = db.execute(text("""
        SELECT id, device_fingerprint, ip_address, license_key, created_at
        FROM trial_devices
        ORDER BY created_at DESC
    """)).fetchall()

    devices = []
    for row in results:
        devices.append({
            "id": row[0],
            "device_fingerprint": row[1],
            "ip_address": row[2],
            "license_key": row[3],
            "created_at": to_iso(row[4])
        })

    return {"devices": devices}

@app.delete("/admin/trial-devices/{device_id}")
def delete_trial_device(device_id: int, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Delete a trial device"""
    db.execute(text("DELETE FROM trial_devices WHERE id = :id"), {"id": device_id})
    db.commit()
    return {"message": "Trial device deleted"}

@app.delete("/admin/trial-devices")
def clear_all_trial_devices(token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Clear all trial devices"""
    db.execute(text("DELETE FROM trial_devices"))
    db.commit()
    return {"message": "All trial devices cleared"}

# ==================== TIERS MANAGEMENT ====================
@app.get("/admin/tiers")
def get_tiers(token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Get all tiers"""
    result = db.execute(text("SELECT * FROM tiers ORDER BY display_order")).fetchall()
    return [{
        "id": r[0],
        "tier_key": r[1],
        "tier_name": r[2],
        "description": r[3],
        "is_active": r[4],
        "display_order": r[5]
    } for r in result]

@app.get("/tiers")
def get_active_tiers(db: Session = Depends(get_db)):
    """Public: Get active tiers for dropdowns"""
    result = db.execute(text("SELECT tier_key, tier_name FROM tiers WHERE is_active=TRUE ORDER BY display_order")).fetchall()
    return [{"value": r[0], "label": r[1]} for r in result]

class TierCreate(BaseModel):
    tier_key: str
    tier_name: str
    description: Optional[str] = None
    is_active: bool = True
    display_order: int = 0

@app.post("/admin/tiers")
def create_tier(tier: TierCreate, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Create new tier"""
    try:
        db.execute(text("""
            INSERT INTO tiers (tier_key, tier_name, description, is_active, display_order)
            VALUES (:key, :name, :desc, :active, :order)
        """), {"key": tier.tier_key, "name": tier.tier_name, "desc": tier.description, "active": tier.is_active, "order": tier.display_order})
        db.commit()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/admin/tiers/{tier_id}")
def update_tier(tier_id: int, tier: TierCreate, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Update tier"""
    db.execute(text("""
        UPDATE tiers SET tier_key=:key, tier_name=:name, description=:desc, is_active=:active, display_order=:order
        WHERE id=:id
    """), {"id": tier_id, "key": tier.tier_key, "name": tier.tier_name, "desc": tier.description, "active": tier.is_active, "order": tier.display_order})
    db.commit()
    return {"success": True}

@app.delete("/admin/tiers/{tier_id}")
def delete_tier(tier_id: int, token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Admin: Delete tier"""
    db.execute(text("DELETE FROM tiers WHERE id=:id"), {"id": tier_id})
    db.commit()
    return {"success": True}


# ==================== WEBSOCKET PAYMENT NOTIFICATION ====================
import asyncio
from typing import Dict, Set

# Store active WebSocket connections by order_id
payment_connections: Dict[str, Set[WebSocket]] = {}

class PaymentConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, order_id: str, websocket: WebSocket):
        await websocket.accept()
        if order_id not in self.active_connections:
            self.active_connections[order_id] = set()
        self.active_connections[order_id].add(websocket)
        print(f"📡 WebSocket connected for order {order_id}")
    
    def disconnect(self, order_id: str, websocket: WebSocket):
        if order_id in self.active_connections:
            self.active_connections[order_id].discard(websocket)
            if not self.active_connections[order_id]:
                del self.active_connections[order_id]
        print(f"📡 WebSocket disconnected for order {order_id}")
    
    async def notify_payment_complete(self, order_id: str, license_key: str, expires_at: str):
        """Notify all connected clients that payment is complete"""
        if order_id in self.active_connections:
            message = {
                "type": "payment_complete",
                "order_id": order_id,
                "license_key": license_key,
                "expires_at": expires_at,
                "message": "Thanh toán thành công! License của bạn đã được kích hoạt."
            }
            disconnected = []
            for websocket in self.active_connections[order_id]:
                try:
                    await websocket.send_json(message)
                    print(f"✅ Sent license notification to order {order_id}")
                except:
                    disconnected.append(websocket)
            
            # Clean up disconnected
            for ws in disconnected:
                self.active_connections[order_id].discard(ws)

payment_manager = PaymentConnectionManager()

@app.websocket("/ws/payment/{order_id}")
async def websocket_payment_endpoint(websocket: WebSocket, order_id: str):
    """WebSocket endpoint for payment notifications"""
    await payment_manager.connect(order_id, websocket)
    try:
        # Check if order already completed
        from database import get_db
        db = next(get_db())
        order = db.execute(text(
            "SELECT payment_status, license_key FROM orders WHERE order_id=:oid"
        ), {"oid": order_id}).fetchone()
        
        if order and order[0] == 'success' and order[1]:
            # Already paid, send license immediately
            await websocket.send_json({
                "type": "payment_complete",
                "order_id": order_id,
                "license_key": order[1],
                "message": "Đơn hàng đã được thanh toán!"
            })
        
        # Keep connection alive and wait for payment
        while True:
            try:
                # Receive heartbeat or close
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_json({"type": "keepalive"})
    except WebSocketDisconnect:
        payment_manager.disconnect(order_id, websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        payment_manager.disconnect(order_id, websocket)

# Endpoint to check order status (fallback if WebSocket fails)
@app.get("/payment/status/{order_id}")
def check_payment_status(order_id: str, db: Session = Depends(get_db)):
    """Check payment status for an order"""
    order = db.execute(text(
        "SELECT payment_status, license_key, tier, duration_days FROM orders WHERE order_id=:oid"
    ), {"oid": order_id}).fetchone()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {
        "order_id": order_id,
        "status": order[0],
        "license_key": order[1],
        "tier": order[2],
        "duration_days": order[3]
    }

# ==================== PAYMENT MANAGER (Restored) ====================
class PaymentManager:
    def __init__(self):
        self.active_connections: List[dict] = []

    async def connect(self, websocket: WebSocket, order_id: str):
        await websocket.accept()
        self.active_connections.append({"ws": websocket, "order_id": order_id})

    def disconnect(self, order_id: str, websocket: WebSocket):
        self.active_connections = [c for c in self.active_connections if c["ws"] != websocket]

    async def notify_payment_complete(self, order_id: str, license_key: str, expires_at: str):
        message = {
            "type": "PAYMENT_COMPLETE",
            "order_id": order_id,
            "license_key": license_key,
            "expires_at": expires_at
        }
        for conn in self.active_connections:
            if conn["order_id"] == order_id:
                try:
                    await conn["ws"].send_json(message)
                except:
                    pass

# Ensure payment_manager exists (if it was deleted)
try:
    payment_manager
except NameError:
    payment_manager = PaymentManager()

