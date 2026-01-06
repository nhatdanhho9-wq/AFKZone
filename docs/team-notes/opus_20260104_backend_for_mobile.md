From: Opus Team
To: Codex Team
Date: 2026-01-04
Subject: Backend for Mobile UX - Complete ✅

Status: COMPLETE
Commit: b230e044a
Pushed: origin/main

## 1) Purchase History ✅
**Endpoint:** GET /user/purchase-history?device_id=xxx

**Sample Response:**
```json
{
  "orders": [
    {
      "id": 123,
      "trans_code": "AFKPRO90260104001",
      "tier": "pro",
      "duration_days": 90,
      "amount": 299000,
      "status": "paid",
      "license_key": "AFK-PRO-XXXXXXXX",
      "created_at": "2026-01-04T10:30:00Z",
      "paid_at": "2026-01-04T10:35:00Z",
      "devices_used": 1,
      "devices_max": 2
    }
  ]
}
```

## 2) Activation History ✅
**Endpoint:** GET /user/activation-history?device_id=xxx

**Sample Response:**
```json
{
  "device_id": "abc123...",
  "activations": [
    {
      "license_key": "AFK-PRO-XXXXXXXX",
      "tier": "pro",
      "expires_at": "2026-04-04T10:35:00Z",
      "activated_at": "2026-01-04T10:36:00Z",
      "devices_max": 2,
      "devices_used": 1,
      "status": "active"
    }
  ]
}
```

## 3) Device List ✅
**Endpoint:** GET /api/devices/list?device_id=xxx

**Sample Response:**
```json
{
  "devices": [
    {
      "device_id": "abc123...",
      "alias": "Laptop Work",
      "last_seen": "2026-01-04T12:00:00Z"
    }
  ]
}
```

## 4) Clear Device Slot ✅
**Endpoint:** DELETE /api/license/device/{device_id}/clear?license_key=xxx

**Sample Response:**
```json
{
  "success": true,
  "message": "Device removed from license",
  "license_key": "AFK-PRO-XXXXXXXX",
  "device_id": "abc123...",
  "devices_used": 0,
  "devices_max": 2
}
```

## 5) Regions ✅
**Endpoint:** GET /public/regions

**Sample Response:**
```json
{
  "regions": [
    {
      "id": "default",
      "display_name": "Vietnam (Default)",
      "id_server": "id.afkzone.cloud",
      "relay_server": "id.afkzone.cloud",
      "key": "EXOW136uTrC0PYYrkavoJH7SjkFlzPjB+vzzpvjsybw=",
      "enabled": true,
      "sort_order": 0
    }
  ]
}
```

## 6) Renewal Logic ✅
- Different tier → NO auto-activate
- New license created, requires manual activation via /api/license/assign

## Deploy Status

- Commit: b230e044a
- Push: ✅ origin/main
- Production: PENDING (needs deploy server_app.py)

## Files Changed

- server_app.py (+80 lines)

## Endpoints Summary

| Endpoint | Method | Status |
|----------|--------|--------|
| /user/purchase-history | GET | ✅ |
| /user/activation-history | GET | ✅ NEW |
| /api/devices/list | GET | ✅ |
| /api/license/device/{id}/clear | DELETE | ✅ NEW |
| /public/regions | GET | ✅ |
| /api/license/assign | POST | ✅ |
| /api/license/{key}/slots | GET | ✅ |
| /api/license/device/{id}/alias | PATCH | ✅ |
