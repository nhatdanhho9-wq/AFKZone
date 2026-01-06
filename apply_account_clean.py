#!/usr/bin/env python3
"""
Apply account-based endpoints to app.py - CLEAN VERSION
Only adds user auth + user endpoints, does NOT modify products
"""

# Read current app.py
with open('/app/app.py', 'r') as f:
    content = f.read()

# Check if bcrypt is imported
if 'import bcrypt' not in content:
    # Add after load_dotenv
    content = content.replace(
        'load_dotenv()\n',
        'load_dotenv()\nimport bcrypt\n',
        1
    )
    print("Added bcrypt import")

# Check if endpoints already exist
if '@app.post("/auth/register")' in content:
    print("User auth endpoints already exist, skipping...")
else:
    # User auth + account endpoints code - using raw string to avoid escaping issues
    USER_ENDPOINTS = '''

# ==================== USER AUTHENTICATION (Account-Based) ====================
USER_JWT_SECRET = JWT_SECRET
USER_JWT_ALGORITHM = "HS256"
USER_JWT_EXPIRE_HOURS = 24 * 30

class UserRegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

class UserLoginRequest(BaseModel):
    email: str
    password: str

def create_user_token(user_id: int, email: str) -> str:
    from jose import jwt
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=USER_JWT_EXPIRE_HOURS),
        "type": "user"
    }
    return jwt.encode(payload, USER_JWT_SECRET, algorithm=USER_JWT_ALGORITHM)

def verify_user_token(authorization: str = Header(None)):
    from jose import jwt
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")
        payload = jwt.decode(token, USER_JWT_SECRET, algorithms=[USER_JWT_ALGORITHM])
        if payload.get("type") != "user":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token: " + str(e))

@app.post("/auth/register")
def user_register(req: UserRegisterRequest, db: Session = Depends(get_db)):
    existing = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": req.email.lower()}).fetchone()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    password_hash = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    result = db.execute(text("INSERT INTO users (email, password_hash, name, created_at) VALUES (:email, :hash, :name, NOW()) RETURNING id"),
                        {"email": req.email.lower(), "hash": password_hash, "name": req.name})
    db.commit()
    user_id = result.fetchone()[0]
    token = create_user_token(user_id, req.email.lower())
    return {"success": True, "user_id": user_id, "email": req.email.lower(), "token": token}

@app.post("/auth/login")
def user_login(req: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.execute(text("SELECT id, email, password_hash, name FROM users WHERE email = :email AND is_active = TRUE"), {"email": req.email.lower()}).fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not bcrypt.checkpw(req.password.encode(), user[2].encode()):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    db.execute(text("UPDATE users SET last_login = NOW() WHERE id = :id"), {"id": user[0]})
    db.commit()
    return {"success": True, "user_id": user[0], "email": user[1], "name": user[3], "token": create_user_token(user[0], user[1])}

@app.get("/auth/me")
def get_current_user(user: dict = Depends(verify_user_token), db: Session = Depends(get_db)):
    user_data = db.execute(text("SELECT id, email, name, created_at, last_login FROM users WHERE id = :id"), {"id": user["user_id"]}).fetchone()
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user_data[0], "email": user_data[1], "name": user_data[2], 
            "created_at": user_data[3].isoformat() if user_data[3] else None, 
            "last_login": user_data[4].isoformat() if user_data[4] else None}

@app.get("/user/licenses")
def get_user_licenses(user: dict = Depends(verify_user_token), db: Session = Depends(get_db)):
    licenses = db.execute(text("""
        SELECT l.license_key, l.tier, l.duration_days, l.expires_at, l.is_active, l.max_devices,
               (SELECT COUNT(*) FROM license_devices WHERE license_key = l.license_key) as devices_used, l.created_at
        FROM licenses l WHERE l.user_id = :user_id ORDER BY l.created_at DESC
    """), {"user_id": user["user_id"]}).fetchall()
    result = []
    for lic in licenses:
        expires = lic[3]
        is_expired = expires < datetime.now() if expires else True
        status = "expired" if is_expired else ("active" if lic[4] else "inactive")
        result.append({"license_key": lic[0], "tier": lic[1], "duration_days": lic[2], 
                       "expires_at": expires.isoformat() if expires else None,
                       "status": status, "devices_max": lic[5] if lic[5] else 1, 
                       "devices_used": lic[6], "created_at": lic[7].isoformat() if lic[7] else None})
    return {"licenses": result}

@app.get("/user/activation-history")
def get_user_activation_history(device_id: str, user: dict = Depends(verify_user_token), db: Session = Depends(get_db)):
    history = db.execute(text("""
        SELECT ld.license_key, l.tier, l.expires_at, ld.activated_at, l.max_devices, l.is_active,
               (SELECT COUNT(*) FROM license_devices WHERE license_key = l.license_key) as devices_used
        FROM license_devices ld JOIN licenses l ON ld.license_key = l.license_key
        WHERE ld.device_id = :device_id AND l.user_id = :user_id ORDER BY ld.activated_at DESC
    """), {"device_id": device_id, "user_id": user["user_id"]}).fetchall()
    result = []
    for h in history:
        expires = h[2]
        is_expired = expires < datetime.now() if expires else True
        status = "expired" if is_expired else ("active" if h[5] else "inactive")
        result.append({"license_key": h[0], "tier": h[1], "expires_at": expires.isoformat() if expires else None,
                       "activated_at": h[3].isoformat() if h[3] else None, 
                       "devices_max": h[4] if h[4] else 1, "devices_used": h[6], "status": status})
    return {"device_id": device_id, "activations": result}

@app.get("/user/devices")
def get_user_devices(user: dict = Depends(verify_user_token), db: Session = Depends(get_db)):
    devices = db.execute(text("""
        SELECT DISTINCT ld.device_id, ld.alias, ld.last_seen, ld.activated_at, ld.license_key, l.tier
        FROM license_devices ld JOIN licenses l ON ld.license_key = l.license_key
        WHERE l.user_id = :user_id ORDER BY ld.last_seen DESC NULLS LAST
    """), {"user_id": user["user_id"]}).fetchall()
    result = []
    for d in devices:
        result.append({"device_id": d[0], "alias": d[1], 
                       "last_seen": d[2].isoformat() if d[2] else None,
                       "activated_at": d[3].isoformat() if d[3] else None, 
                       "license_key": d[4], "tier": d[5]})
    return {"devices": result}

@app.delete("/user/devices/{device_id}/clear")
def clear_user_device(device_id: str, user: dict = Depends(verify_user_token), db: Session = Depends(get_db)):
    device = db.execute(text("""
        SELECT ld.license_key FROM license_devices ld JOIN licenses l ON ld.license_key = l.license_key
        WHERE ld.device_id = :device_id AND l.user_id = :user_id
    """), {"device_id": device_id, "user_id": user["user_id"]}).fetchone()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found or not owned by user")
    db.execute(text("DELETE FROM license_devices WHERE device_id = :device_id"), {"device_id": device_id})
    db.commit()
    return {"success": True, "message": "Device removed", "device_id": device_id}

class AliasRequest(BaseModel):
    alias: str

@app.patch("/user/devices/{device_id}/alias")
def update_device_alias(device_id: str, req: AliasRequest, user: dict = Depends(verify_user_token), db: Session = Depends(get_db)):
    device = db.execute(text("""
        SELECT ld.license_key FROM license_devices ld JOIN licenses l ON ld.license_key = l.license_key
        WHERE ld.device_id = :device_id AND l.user_id = :user_id
    """), {"device_id": device_id, "user_id": user["user_id"]}).fetchone()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    db.execute(text("UPDATE license_devices SET alias = :alias WHERE device_id = :device_id"), {"alias": req.alias, "device_id": device_id})
    db.commit()
    return {"success": True, "device_id": device_id, "alias": req.alias}
'''
    
    # Add before if __name__ == "__main__"
    if 'if __name__ ==' in content:
        content = content.replace('if __name__ ==', USER_ENDPOINTS + '\n\nif __name__ ==')
    else:
        content = content + USER_ENDPOINTS
    
    print("Added user auth and account endpoints")

# Write updated content
with open('/app/app.py', 'w') as f:
    f.write(content)

print("\\n=== APPLY COMPLETE ===")
print("Endpoints added:")
print("- POST /auth/register")
print("- POST /auth/login")
print("- GET /auth/me")
print("- GET /user/licenses")
print("- GET /user/activation-history")
print("- GET /user/devices")
print("- DELETE /user/devices/{device_id}/clear")
print("- PATCH /user/devices/{device_id}/alias")
