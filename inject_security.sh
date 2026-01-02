#!/bin/bash
# Security patch for admin login lockout
# This script injects lockout logic into /app/app.py

set -e

APP_FILE="/app/app.py"
BACKUP_FILE="/app/app.py.bak"

# Backup original
cp $APP_FILE $BACKUP_FILE

# Add security imports after existing imports (after "from fastapi" imports)
# First, create the security code block
cat > /tmp/security_block.py << 'SECURITY_CODE'
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
    if ip in _lockouts and time.time() < _lockouts[ip]:
        return True
    return False

def record_failed_login(ip: str, username: str):
    now = time.time()
    security_logger.warning(f"Failed admin login: username={username} ip={ip}")
    if ip not in _failed_logins:
        _failed_logins[ip] = []
    _failed_logins[ip].append((now, username))
    _failed_logins[ip] = [(t, u) for t, u in _failed_logins[ip] if now - t < LOCKOUT_WINDOW]
    if len(_failed_logins[ip]) >= LOCKOUT_THRESHOLD:
        _lockouts[ip] = now + LOCKOUT_DURATION
        security_logger.warning(f"IP locked out: ip={ip}")

def clear_failed_logins(ip: str):
    if ip in _failed_logins:
        del _failed_logins[ip]
SECURITY_CODE

# Insert after line 1 (after #!/usr/bin/env python or first import)
head -1 $APP_FILE > /tmp/new_app.py
cat /tmp/security_block.py >> /tmp/new_app.py
tail -n +2 $APP_FILE >> /tmp/new_app.py

mv /tmp/new_app.py $APP_FILE

echo "Security code injected into $APP_FILE"
echo "Backup saved to $BACKUP_FILE"
