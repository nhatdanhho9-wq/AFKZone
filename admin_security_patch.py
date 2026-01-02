#!/usr/bin/env python3
"""
Admin Login Security Patch
Adds lockout logic and failed login logging to /app/app.py
"""

# Security constants to add near imports
SECURITY_IMPORTS = '''
import time
import logging

# Security logging
logging.basicConfig(level=logging.INFO)
security_logger = logging.getLogger("admin_security")

# Failed login tracking
_failed_logins = {}  # {ip: [(timestamp, username), ...]}
LOCKOUT_THRESHOLD = 10  # failures in window
LOCKOUT_WINDOW = 900    # 15 minutes
LOCKOUT_DURATION = 1800 # 30 minutes
_lockouts = {}  # {ip: lockout_until}

def check_lockout(ip: str) -> bool:
    """Check if IP is currently locked out"""
    if ip in _lockouts and time.time() < _lockouts[ip]:
        return True
    return False

def record_failed_login(ip: str, username: str):
    """Record failed login attempt and apply lockout if threshold reached"""
    now = time.time()
    security_logger.warning(f"Failed admin login: username={username} ip={ip}")
    
    if ip not in _failed_logins:
        _failed_logins[ip] = []
    
    # Add new attempt and clean old ones
    _failed_logins[ip].append((now, username))
    _failed_logins[ip] = [(t, u) for t, u in _failed_logins[ip] if now - t < LOCKOUT_WINDOW]
    
    # Check threshold
    if len(_failed_logins[ip]) >= LOCKOUT_THRESHOLD:
        _lockouts[ip] = now + LOCKOUT_DURATION
        security_logger.warning(f"IP locked out: ip={ip} until={now + LOCKOUT_DURATION}")

def clear_failed_logins(ip: str):
    """Clear failed logins on success"""
    if ip in _failed_logins:
        del _failed_logins[ip]
'''

# Updated admin_login function
NEW_ADMIN_LOGIN = '''
@app.post("/admin/login")
def admin_login(req: AdminLoginRequest, request: Request, db: Session = Depends(get_db)):
    """Admin login - returns JWT token with lockout protection"""
    ip = request.client.host if request.client else "unknown"
    
    # Check lockout
    if check_lockout(ip):
        remaining = int(_lockouts.get(ip, 0) - time.time())
        raise HTTPException(
            status_code=429, 
            detail=f"Too many failed attempts. Try again in {remaining // 60} minutes."
        )
    
    result = db.execute(
        text("SELECT * FROM admin_users WHERE username=:username"),
        {"username": req.username}
    ).fetchone()

    if not result:
        record_failed_login(ip, req.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password (bcrypt)
    if not bcrypt.checkpw(req.password.encode(), result[2].encode()):
        record_failed_login(ip, req.username)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Success - clear failed attempts
    clear_failed_logins(ip)
    security_logger.info(f"Admin login success: username={result[1]} ip={ip}")
    
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
'''

print("Security patch content ready for injection")
print("SECURITY_IMPORTS length:", len(SECURITY_IMPORTS))
print("NEW_ADMIN_LOGIN length:", len(NEW_ADMIN_LOGIN))
