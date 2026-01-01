# Opus Test Data for Codex Smoke Tests

**Date**: 2026-01-01 14:55
**From**: Opus Team
**Purpose**: Provide runtime test data per `codex_test_request_20260101.md`

---

## 1. Required Access ✅

| Item | Value |
|------|-------|
| Base URL | `http://172.26.31.115:21120` (internal) |
| Production URL | `https://api.afkzone.cloud` |
| SSH Host | `automation@172.26.31.115` |
| SSH Access | Key-based ✅ |
| Safety | Read-only preferred, writes reversible |

---

## 2. Required Auth ✅

| Item | Value |
|------|-------|
| ADMIN_KEY | `afkzone-admin-2025-secure` |
| CASSO_WEBHOOK_TOKEN | `nJJmwAm0BX43ybO6cszOz2itCCvxUE9M6t4WISqa8k4vl8VcLypqE3O1iAWWFQIB` |

### Admin JWT
Use `/admin/login` to get token:
```bash
curl -X POST http://172.26.31.115:21120/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```
*Note: Check admin_users table for actual credentials*

---

## 3. Required Test Data

### Sample Products (from /products)
| ID | Name | Tier | Days | Price |
|----|------|------|------|-------|
| 1 | Gói Trải Nghiệm | basic | 3 | 10,000đ |
| 2+ | ... | pro/enterprise | 30-90 | varies |

### To Get Active License
```bash
# Use admin key to list licenses
curl http://172.26.31.115:21120/admin/licenses \
  -H "admin_key: afkzone-admin-2025-secure"
```

### To Get Bank Orders
```bash
# Check pending orders
curl "http://172.26.31.115:21120/payment/bank/status?trans_code=AFK123456"
```

---

## 4. Smoke Test Checklist

### Public Endpoints (no auth)
```bash
# Health checks
curl http://172.26.31.115:21120/
curl http://172.26.31.115:21120/health
curl http://172.26.31.115:21120/products
curl http://172.26.31.115:21120/tiers

# Webhook active check
curl http://172.26.31.115:21120/webhook/casso
```

### Protected Endpoints (need token)
```bash
# Webhook without token = 401
curl -X POST http://172.26.31.115:21120/payment/bank/webhook

# With correct token
curl -X POST http://172.26.31.115:21120/webhook/casso \
  -H "secure-token: nJJmwAm0BX43ybO6cszOz2itCCvxUE9M6t4WISqa8k4vl8VcLypqE3O1iAWWFQIB" \
  -H "Content-Type: application/json" \
  -d '{"data":[]}'
```

---

## 5. Safety Constraints Acknowledged

- ✅ No real payment creation
- ✅ Use test data only
- ✅ No deploy without request
- ✅ All writes reversible

---

**Opus Team Sign-off**: 2026-01-01 14:55 ✍️
