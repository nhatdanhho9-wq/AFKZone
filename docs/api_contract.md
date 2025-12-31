# AFK Zone API Contract

> Single source of truth for client-server API communication.

## Canonical Field Names

| Field | Type | Description |
|-------|------|-------------|
| `license_key` | string | License key (AFK-xxxxx format) |
| `device_id` | string | SHA256 hash of device fingerprint |
| `max_devices` | int | Maximum devices allowed (-1 = unlimited) |
| `expires_at` | int | Unix timestamp in milliseconds |
| `tier` | string | Tier key (basic, pro, enterprise) |

## Client SharedPreferences Keys

| Key | Type | Description |
|-----|------|-------------|
| `license_key` | string | Current license key |
| `device_id` | string | Device fingerprint |
| `afk_license_active` | bool | License is active |
| `afk_license_expires_at` | int | Expiry timestamp (ms) |
| `afk_max_devices` | int | Max devices |
| `afk_license_tier` | string | Tier name |

---

## Public Endpoints (No Auth)

### License Management

| Method | Endpoint | Status | Client Usage |
|--------|----------|--------|--------------|
| POST | `/activate` | ✅ Active | license_service.dart:87 |
| POST | `/check` | ✅ Active | license_service.dart:117 |
| GET | `/license/info` | ✅ Active | license_service.dart:214 |
| POST | `/license/logout` | ✅ Active | license_service.dart:187 |
| POST | `/license/recover` | ✅ Active | license_service.dart:255 |

### Trial

| Method | Endpoint | Status | Client Usage |
|--------|----------|--------|--------------|
| POST | `/trial/check` | ✅ Active | license_service.dart:38 |
| POST | `/trial/generate` | ✅ Active | license_service.dart:59 |

### Payment

| Method | Endpoint | Status | Client Usage |
|--------|----------|--------|--------------|
| POST | `/payment/create` | ✅ Active | license_service.dart:161 (ZaloPay) |
| POST | `/payment/bank/create` | ✅ Active | payment_service.dart:16 |
| GET | `/payment/bank/status` | ✅ Active | payment_service.dart:42 |
| POST | `/payment/bank/webhook` | ✅ Active | (Casso callback) |
| POST | `/webhook/casso` | ✅ Active | (Casso callback alt) |

### Products & Tiers

| Method | Endpoint | Status | Client Usage |
|--------|----------|--------|--------------|
| GET | `/products` | ✅ Active | product_service.dart:12 |
| GET | `/tiers` | ✅ Active | product_service.dart:83 |

### Misc

| Method | Endpoint | Status | Client Usage |
|--------|----------|--------|--------------|
| GET | `/version/check` | ✅ Active | license_service.dart:140 |
| GET | `/notifications` | ✅ Active | notification_service.dart:13 |
| POST | `/connection/log` | ✅ Active | license_service.dart:283 |
| POST | `/heartbeat` | ✅ Active | (background) |
| GET | `/user/history` | ✅ Active | license_service.dart:234 |

---

## Admin Endpoints (Require Auth)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/admin/login` | Admin authentication |
| GET | `/admin` | Dashboard HTML |
| GET | `/admin/dashboard/stats` | Dashboard statistics |

### Licenses
| GET | `/admin/licenses` | List licenses |
| GET | `/admin/licenses/all` | All licenses (detailed) |
| POST | `/admin/licenses/generate` | Create license |
| POST | `/admin/licenses/bulk-create` | Bulk create |
| POST | `/admin/licenses/airdrop` | Airdrop licenses |
| PUT | `/admin/licenses/{key}/extend` | Extend license |
| POST | `/admin/licenses/{key}/revoke` | Revoke license |
| POST | `/admin/licenses/{key}/unrevoke` | Unrevoke |
| DELETE | `/admin/licenses/{key}` | Delete license |

### Products
| GET | `/products` | List products |
| POST | `/admin/products` | Create product |
| PUT | `/admin/products/{id}` | Update product |
| DELETE | `/admin/products/{id}` | Soft delete |
| DELETE | `/admin/products/{id}/permanent` | Hard delete |
| POST | `/admin/products/{id}/enable` | Enable |
| POST | `/admin/products/{id}/disable` | Disable |

### Devices
| GET | `/admin/devices/detailed` | Device list |
| DELETE | `/admin/devices/{id}` | Remove device |
| GET | `/admin/trial-devices` | Trial devices |
| DELETE | `/admin/trial-devices/{id}` | Remove trial device |

### Orders
| GET | `/admin/orders` | List orders |
| POST | `/admin/orders/{trans_code}/complete` | Complete order manually |

### Connections
| GET | `/admin/connections` | Connection logs |

### Notifications
| GET | `/admin/notifications` | List notifications |
| POST | `/admin/notifications` | Create notification |
| DELETE | `/admin/notifications/{id}` | Delete notification |

### Analytics
| GET | `/admin/analytics/revenue` | Revenue stats |

---

## Response Format Standards

### Success Response
```json
{
  "status": "success",
  "license_key": "AFK-xxxxx",
  "tier": "pro",
  "max_devices": 5,
  "expires_at": 1704067200000
}
```

### Error Response
```json
{
  "detail": "Error message here"
}
```

---

## Known Issues (To Fix)

1. **Duplicate route**: `/admin/licenses/{key}/extend` defined twice
2. **expires_at format**: Some endpoints return ISO string, should be epoch_ms
3. **WebSocket**: `/ws/payment/{order_id}` not implemented on server

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-01-01 | Initial contract creation | Codex Plan |
