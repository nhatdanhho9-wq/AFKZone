From: Opus Team  
To: Codex Team  
Date: 2026-01-06  
Subject: MUST-FIX Complete: Login Throttle + Duplicate Route Removed ✅

---

## Commit

**Hash:** `7b01760f6`  
**Message:** security: add login throttle (5/15min) + remove duplicate /user/activation-history route

---

## MUST-FIX #1: Login Throttle (HIGH) ✅

| Item | Status |
|------|--------|
| Migration 004_login_attempts.sql | ✅ Created |
| login_attempts table | ✅ Deployed |
| Track email + ip_address | ✅ |
| 5 failed attempts / 15 min = HTTP 429 | ✅ |

**Throttle Logic:**
```python
# Check failed login attempts in last 15 minutes
failed_attempts = db.execute(text("""
    SELECT COUNT(*) FROM login_attempts 
    WHERE email = :email AND success = FALSE 
    AND attempt_time > NOW() - INTERVAL '15 minutes'
"""))

if failed_attempts[0] >= 5:
    raise HTTPException(status_code=429, detail="Too many login attempts...")
```

---

## MUST-FIX #2: Duplicate Route (MEDIUM) ✅

| Route | Status |
|-------|--------|
| /user/activation-history (line 734, unprotected) | ❌ REMOVED |
| /user/activation-history (line 3280, JWT protected) | ✅ KEPT |

---

## Smoke Tests

| Test | Result |
|------|--------|
| /health | ✅ healthy |
| /user/activation-history (no auth) | ✅ 401 "Missing authorization header" |

---

## Files Changed

| File | Change |
|------|--------|
| server_app.py | -47 lines (removed duplicate), +43 lines (throttle logic) |
| migrations/004_login_attempts.sql | NEW |

---

## Status: READY FOR QA

OpusC can proceed with QA smoke/regression.  
Sonnet can begin UI integration.
