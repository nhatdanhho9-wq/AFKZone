"""
Security lockout module for admin login
Provides failed login tracking, lockout logic, and security logging
"""
import time
import logging

# Security logging
logging.basicConfig(level=logging.INFO)
security_logger = logging.getLogger("admin_security")

# Failed login tracking
_failed_logins = {}  # {ip: [(timestamp, username), ...]}
LOCKOUT_THRESHOLD = 10  # failures in window
LOCKOUT_WINDOW = 900    # 15 minutes in seconds
LOCKOUT_DURATION = 1800 # 30 minutes in seconds
_lockouts = {}  # {ip: lockout_until_timestamp}

def check_lockout(ip: str) -> bool:
    """Check if IP is currently locked out"""
    if ip in _lockouts and time.time() < _lockouts[ip]:
        return True
    return False

def get_lockout_remaining(ip: str) -> int:
    """Get remaining lockout time in seconds"""
    if ip in _lockouts:
        return max(0, int(_lockouts[ip] - time.time()))
    return 0

def record_failed_login(ip: str, username: str):
    """Record failed login attempt and apply lockout if threshold reached"""
    now = time.time()
    security_logger.warning(f"Failed admin login: username={username} ip={ip}")
    
    if ip not in _failed_logins:
        _failed_logins[ip] = []
    
    # Add new attempt
    _failed_logins[ip].append((now, username))
    
    # Clean old attempts outside window
    _failed_logins[ip] = [(t, u) for t, u in _failed_logins[ip] if now - t < LOCKOUT_WINDOW]
    
    # Check threshold and apply lockout
    if len(_failed_logins[ip]) >= LOCKOUT_THRESHOLD:
        _lockouts[ip] = now + LOCKOUT_DURATION
        security_logger.warning(f"IP locked out: ip={ip} duration={LOCKOUT_DURATION}s")

def clear_failed_logins(ip: str):
    """Clear failed logins on successful authentication"""
    if ip in _failed_logins:
        del _failed_logins[ip]

def log_successful_login(ip: str, username: str):
    """Log successful login"""
    security_logger.info(f"Admin login success: username={username} ip={ip}")
