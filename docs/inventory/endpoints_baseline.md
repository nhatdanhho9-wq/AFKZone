# Endpoint Inventory - Baseline v2.2.42

Generated: 2026-01-01

## Summary
- **Total Server Endpoints**: 60
- **Total Client Calls**: 16
- **Missing on Server**: 0 (all client calls have matching endpoints)
- **Unused on Server**: 44 (admin endpoints not called by client)

---

## Client → Server Mapping

| Client File | Endpoint | Method | Status |
|-------------|----------|--------|--------|
| license_service.dart:38 | /trial/check | POST | ✅ |
| license_service.dart:59 | /trial/generate | POST | ✅ |
| license_service.dart:87 | /activate | POST | ✅ |
| license_service.dart:117 | /check | POST | ✅ |
| license_service.dart:140 | /version/check | GET | ✅ |
| license_service.dart:161 | /payment/create | POST | ✅ |
| license_service.dart:187 | /license/logout | POST | ✅ |
| license_service.dart:214 | /license/info | GET | ✅ |
| license_service.dart:234 | /user/history | GET | ✅ |
| license_service.dart:255 | /license/recover | POST | ✅ |
| license_service.dart:283 | /connection/log | POST | ✅ |
| payment_service.dart:16 | /payment/bank/create | POST | ✅ |
| payment_service.dart:42 | /payment/bank/status | GET | ✅ |
| product_service.dart:12 | /products | GET | ✅ |
| product_service.dart:83 | /tiers | GET | ✅ |
| notification_service.dart:13 | /notifications | GET | ✅ |

---

## Server-Only Endpoints (Admin)

### Authentication
- POST /admin/login

### Licenses
- GET /admin/licenses
- GET /admin/licenses/all
- POST /admin/licenses/generate
- POST /admin/licenses/bulk-create
- POST /admin/licenses/airdrop
- PUT /admin/licenses/{key}/extend (duplicate)
- POST /admin/licenses/{key}/revoke
- POST /admin/licenses/{key}/unrevoke
- DELETE /admin/licenses/{key}

### Products
- POST /admin/products
- PUT /admin/products/{id}
- DELETE /admin/products/{id}
- DELETE /admin/products/{id}/permanent
- POST /admin/products/{id}/enable
- POST /admin/products/{id}/disable

### Orders
- GET /admin/orders
- POST /admin/orders/{trans_code}/complete

### Devices
- GET /admin/devices/detailed
- DELETE /admin/devices/{device_id}
- GET /admin/trial-devices
- DELETE /admin/trial-devices/{id}
- DELETE /admin/trial-devices (bulk)

### Connections
- GET /admin/connections

### Notifications
- GET /admin/notifications
- POST /admin/notifications
- DELETE /admin/notifications/{id}

### Analytics
- GET /admin/dashboard/stats
- GET /admin/analytics/revenue

### Webhooks
- GET /payment/bank/webhook (test)
- POST /payment/bank/webhook (Casso)
- GET /webhook/casso (test)
- POST /webhook/casso (Casso)

### Misc
- GET / (root)
- GET /health
- POST /heartbeat
- GET /admin (dashboard HTML)

---

## Issues Found
1. **Duplicate route**: `/admin/licenses/{key}/extend` appears twice (line ~37 and ~39 in grep output)
2. **WebSocket missing**: Client expects `/ws/payment/{order_id}` but not implemented
3. **Connection log mismatch**: Client sends JSON to `/connection/log`, server may expect query params

---

## Recommendations
1. Remove duplicate `/admin/licenses/{key}/extend`
2. Decide: implement WebSocket or remove client code
3. Standardize connection logging format
