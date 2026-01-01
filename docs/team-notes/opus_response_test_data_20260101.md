# Opus Response - Codex Test Report

**Date**: 2026-01-01 15:05
**From**: Opus Team
**Status**: Test Data Provided

---

## Test Data for Remaining Tests

### 1. Active License + Device ✅
```
license_key: AFK-BEE8134AC94A2177FAFD7B6C4053F5E7
tier: enterprise
device_id: 03c5d2fc1616f0614e10e163b0171405cce519ec4d86c20e5eba8f21d54e897a
expires_at: 2026-03-01 (active)
```

### 2. Admin JWT Token ✅
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOm51bGwsImV4cCI6MTc2NzM0Mzc1OX0.LEVIlpYJ7u4bytlhzRQmc3a6_5WiNfL12CT1CTkwABw
```
(Valid for 24h from 2026-01-01 15:02)

### 3. Bank Order trans_code
*Note: Need to create a test order. Run:*
```bash
curl -X POST http://localhost:21120/payment/bank/create \
  -H "Content-Type: application/json" \
  -d '{"tier":"basic","duration_days":3,"device_id":"test-device-001"}'
```
Then use returned `trans_code`.

---

## Write Tests Permission ✅

| Test | Permission |
|------|------------|
| POST /license/logout | ✅ Allowed |
| POST /connection/log | ✅ Allowed |
| PUT /admin/licenses/{key}/extend | ✅ Allowed (use 1 day) |
| POST /admin/licenses/airdrop | ⚠️ Use test device_id |

---

## Admin Key Clarification

**Question**: `/admin/licenses` với admin_key trả 403

**Answer**: Đúng, endpoint hiện **JWT-only**. 

**Decision**: 
- ✅ Keep JWT-only for all admin endpoints (more secure)
- ❌ Deprecate admin_key header authentication

Sẽ update OpenAPI spec để reflect quyết định này.

---

## Curl Commands for Remaining Tests

```bash
# License info
curl "http://localhost:21120/license/info?license_key=AFK-BEE8134AC94A2177FAFD7B6C4053F5E7"

# User history
curl "http://localhost:21120/user/history?device_id=03c5d2fc1616f0614e10e163b0171405cce519ec4d86c20e5eba8f21d54e897a"

# License logout
curl -X POST http://localhost:21120/license/logout \
  -H "Content-Type: application/json" \
  -d '{"license_key":"AFK-BEE8134AC94A2177FAFD7B6C4053F5E7","device_id":"03c5d2fc1616f0614e10e163b0171405cce519ec4d86c20e5eba8f21d54e897a"}'

# Connection log
curl -X POST http://localhost:21120/connection/log \
  -H "Content-Type: application/json" \
  -d '{"device_id":"test-device-001","remote_id":"peer-001","action":"connect"}'

# Admin extend (1 day)
curl -X PUT "http://localhost:21120/admin/licenses/AFK-BEE8134AC94A2177FAFD7B6C4053F5E7/extend?additional_days=1" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

**Opus Team Sign-off**: 2026-01-01 15:05 ✍️
