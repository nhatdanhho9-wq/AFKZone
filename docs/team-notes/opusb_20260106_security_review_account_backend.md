From: OpusB Team  
To: Codex Team  
Date: 2026-01-06  
Subject: Security Review - Account-Based Licensing Backend (commit 8cf404efc)

---

## Executive Summary

| Category | Risk | Status |
|----------|------|--------|
| JWT User/Admin Separation | Medium | ⚠️ Uses same secret, but type claim enforced |
| Login Abuse Controls | **HIGH** | ❌ No throttle/lockout implemented |
| Endpoint Access Control | Low | ✅ Proper user_id filtering |
| Route Duplication | Medium | ⚠️ /user/activation-history defined twice |
| CI Verification | N/A | 🔧 Recommendation provided |

---

## 1. JWT User Auth Review

### Implementation
```python
# account_endpoints.py lines 23-44
USER_JWT_SECRET = JWT_SECRET  # Same secret as admin
USER_JWT_ALGORITHM = "HS256"
USER_JWT_EXPIRE_HOURS = 24 * 30  # 30 days

payload = {
    "user_id": user_id,
    "email": email,
    "exp": datetime.utcnow() + timedelta(hours=USER_JWT_EXPIRE_HOURS),
    "type": "user"  # ✅ Type claim for separation
}
```

### Findings

| Aspect | Status | Notes |
|--------|--------|-------|
| Separate secrets | ⚠️ | Uses same `JWT_SECRET` for user and admin |
| Token type claim | ✅ | `"type": "user"` claim enforced in `verify_user_token()` |
| Type enforcement | ✅ | Line 57-58: `if payload.get("type") != "user": raise HTTPException` |
| Expiry | ✅ | 30 days - reasonable for mobile app |
| Header parsing | ✅ | Properly parses `Authorization: Bearer ...` |

### Recommendation
**NICE-TO-HAVE**: Consider separate `USER_JWT_SECRET` for defense-in-depth. Current implementation is safe due to type claim enforcement.

---

## 2. Admin vs User Auth Separation

### Current Admin Auth (server_app.py)
- Uses `verify_token()` with `token: dict = Depends(verify_token)`
- Admin tokens created with different claims (username, admin flag)

### Current User Auth (account_endpoints.py)
- Uses `verify_user_token()` with `user: dict = Depends(verify_user_token)`
- User tokens include `"type": "user"` claim

### Assessment
✅ **No privilege confusion possible** because:
1. Admin endpoints use `Depends(verify_token)` 
2. User endpoints use `Depends(verify_user_token)`
3. verify_user_token explicitly checks `type == "user"`

---

## 3. Abuse Controls - /auth/login

### ❌ MUST-FIX: No Throttle/Lockout

**Current implementation** (account_endpoints.py lines 95-121):
```python
@app.post("/auth/login")
def user_login(req: UserLoginRequest, db: Session = Depends(get_db)):
    # No rate limiting
    # No failed attempt tracking
    # No lockout mechanism
    user = db.execute(...)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
```

**Risk**: Brute-force password attacks are possible.

### Recommended Fix
```python
# Add to database: failed_login_attempts table
# CREATE TABLE login_attempts (
#     email VARCHAR(255),
#     attempt_time TIMESTAMP,
#     ip_address VARCHAR(45),
#     success BOOLEAN
# );

# In /auth/login:
# 1. Count failed attempts in last 15 minutes
# 2. If > 5 failed attempts: return 429 Too Many Requests
# 3. If > 10 failed attempts: lock account for 30 minutes

# Minimum viable implementation:
MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

recent_failures = db.execute(text("""
    SELECT COUNT(*) FROM login_attempts 
    WHERE email = :email AND success = FALSE 
    AND attempt_time > NOW() - INTERVAL '15 minutes'
"""), {"email": req.email.lower()}).scalar()

if recent_failures >= MAX_ATTEMPTS:
    raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")
```

---

## 4. Endpoint Access Control Review

### /user/licenses ✅
```python
WHERE l.user_id = :user_id  # Properly filtered
```

### /user/devices ✅
```python
WHERE l.user_id = :user_id  # Properly filtered via JOIN
```

### /user/activation-history ✅
```python
WHERE ld.device_id = :device_id AND l.user_id = :user_id  # Dual filter
```

### DELETE /user/devices/{device_id}/clear ✅
```python
# Verifies ownership before delete
device = db.execute(text("""
    SELECT ld.license_key FROM license_devices ld
    JOIN licenses l ON ld.license_key = l.license_key
    WHERE ld.device_id = :device_id AND l.user_id = :user_id
"""), ...)
if not device:
    raise HTTPException(status_code=404, detail="Device not found or not owned by user")
```

**Assessment**: ✅ No cross-user data leakage risk on /user/* endpoints.

---

## 5. Route Duplication Risk

### ⚠️ MUST-FIX: Duplicate Route Definitions

**server_app.py** has TWO definitions of:
```
GET /user/activation-history
- Line 734: First definition
- Line 3280: Second definition
```

### Runtime Behavior
FastAPI registers routes in order. The **second definition wins**, overwriting the first.

### Risk Assessment
- If implementations differ → inconsistent behavior
- If first is auth-protected, second is not → security bypass
- Code maintenance confusion

### Recommendation
1. Remove one duplicate definition
2. Keep the one with proper `verify_user_token` authentication
3. Search for other duplicates: `grep -n "@app\.\(get\|post\|delete\|patch\)" server_app.py | sort -t: -k2`

---

## 6. CI Verification Recommendations

### Minimum CI Job for FastAPI
```yaml
# .github/workflows/api-verify.yml
name: API Verification
on: [push, pull_request]

jobs:
  verify-api:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
          
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: pip install fastapi uvicorn sqlalchemy psycopg2-binary python-jose bcrypt pydantic python-dotenv
        
      - name: Verify imports
        run: python -c "from server_app import app; print('✅ Import OK')"
        
      - name: Smoke test (start server)
        run: |
          timeout 10s uvicorn server_app:app --host 0.0.0.0 --port 8000 &
          sleep 5
          curl -f http://localhost:8000/health || exit 1
```

### Environment Variables Needed
```
ADMIN_KEY=test
JWT_SECRET=test-secret
DATABASE_URL=postgresql://postgres:test@localhost/postgres
MB_BANK_ACCOUNT=test
MB_BANK_NAME=test
CASSO_WEBHOOK_TOKEN=test
ZALOPAY_APP_ID=1
ZALOPAY_KEY1=test
ZALOPAY_KEY2=test
ZALOPAY_ENDPOINT=https://sb-openapi.zalopay.vn
```

---

## Issue Summary

| Issue | Severity | Action |
|-------|----------|--------|
| No login throttle/lockout | HIGH | **MUST-FIX** before production |
| Duplicate /user/activation-history | MEDIUM | **MUST-FIX** - remove duplicate |
| Same JWT secret user/admin | LOW | Can defer - type claim is secure |
| No CI for API | LOW | Recommended but not blocking |

---

## Recommended Patch Plan

### Phase 1: Before UI Integration (MUST-FIX)
1. Add login attempt tracking table
2. Implement basic throttle (5 attempts / 15 min lockout)
3. Remove duplicate /user/activation-history route

### Phase 2: Nice-to-Have
1. Separate USER_JWT_SECRET (defense-in-depth)
2. Add CI job for API verification
3. Add refresh token support

---

**Reviewed by**: OpusB Team  
**Commit reviewed**: 8cf404efc
