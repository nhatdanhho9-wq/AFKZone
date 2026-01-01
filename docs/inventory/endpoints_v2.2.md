# Endpoint Inventory - v2.2 (Frozen)

Generated: 2026-01-01
Status: **Official Contract**

## Canonical Standards
- **Date/Time**: ISO 8601 (e.g., `2023-10-27T10:00:00`)
- **Webhook**: `/webhook/casso` (Strict `secure-token` header)
- **Auth**:
  - Admin Scripts: `admin_key` (via `ADMIN_KEY` env)
  - Dashboard/Client: `Authorization: Bearer <JWT>`

## Client → Server Mapping

| Client File | Endpoint | Method | Status | Notes |
|-------------|----------|--------|--------|-------|
| license_service.dart | `/trial/check` | POST | Active | |
| license_service.dart | `/trial/generate` | POST | Active | |
| license_service.dart | `/activate` | POST | Active | |
| license_service.dart | `/activate-v2` | POST | Active | Recommended for multidevice |
| license_service.dart | `/check` | POST | Active | |
| license_service.dart | `/version/check` | GET | Active | |
| license_service.dart | `/payment/create` | POST | Active | ZaloPay |
| license_service.dart | `/license/logout` | POST | Active | |
| license_service.dart | `/license/info` | GET | Active | |
| license_service.dart | `/user/history` | GET | Active | Returns ISO 8601 |
| license_service.dart | `/license/recover` | POST | Active | Returns ISO 8601 |
| license_service.dart | `/connection/log` | POST | Active | |
| payment_service.dart | `/payment/bank/create` | POST | Active | MB Bank |
| payment_service.dart | `/payment/bank/status` | GET | Active | |
| product_service.dart | `/products` | GET | Active | |
| product_service.dart | `/tiers` | GET | Active | |
| notification_service.dart | `/notifications` | GET | Active | |

## Webhooks

| Endpoint | Method | Status | Sign Header | Notes |
|----------|--------|--------|-------------|-------|
| `/webhook/casso` | POST | **Canonical** | `secure-token` | Use this one |
| `/payment/bank/webhook` | POST | **Deprecated** | `x-casso-signature` | Do not use |

## Admin Endpoints (Server Only)

### Licenses
- GET `/admin/licenses` (Legacy)
- GET `/admin/licenses/all` (Dashboard, ISO 8601)
- POST `/admin/licenses/generate`
- POST `/admin/licenses/{key}/revoke`
- POST `/admin/licenses/{key}/unrevoke`
- DELETE `/admin/licenses/{key}`

### Products
- GET `/products`
- POST `/admin/products`
- PUT `/admin/products/{id}`
- DELETE `/admin/products/{id}`
- DELETE `/admin/products/{id}/permanent`
- POST `/admin/products/{id}/enable`
- POST `/admin/products/{id}/disable`

### Orders
- GET `/admin/orders`
- POST `/admin/orders/{trans_code}/complete`

### Devices & Connections
- GET `/admin/devices/detailed` (ISO 8601)
- DELETE `/admin/devices/{device_id}`
- GET `/admin/trial-devices` (ISO 8601)
- DELETE `/admin/trial-devices/{id}`
- DELETE `/admin/trial-devices` (Delete All)
- GET `/admin/connections` (ISO 8601)

### Tiers
- GET `/admin/tiers`
- POST `/admin/tiers`
- PUT `/admin/tiers/{id}`
- DELETE `/admin/tiers/{id}`

### Misc
- GET `/admin/dashboard/stats`
- GET `/admin/analytics/revenue`
- POST `/admin/notifications`
- GET `/admin/notifications`
- DELETE `/admin/notifications/{id}`
