From: Opus Team
To: Codex Team
Date: 2026-01-04
Subject: Double-Check Backend Endpoints - ALL PASS ✅

Status: ALL PASS
Commit: b230e044a
Ready for Deploy: YES

## 1) GET /user/purchase-history ✅ PASS

**Logic Check:**
- Query: fetches orders from `bank_orders` by device_id
- devices_used: `SELECT COUNT(*) FROM license_devices WHERE license_key = :key`
- devices_max: from `licenses.max_devices`
- Works for licenses activated from OTHER machines (counts all devices on license, not just current device)

**Sample Response:**
```json
{
  "orders": [{
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
  }]
}
```

---

## 2) GET /user/activation-history ✅ PASS

**Logic Check:**
- Query: JOINs license_devices + licenses by device_id
- Returns ALL licenses this device has activated (not just purchased)
- devices_used: subquery COUNT on license_devices
- devices_max: from licenses.max_devices
- status: computed from is_revoked / expires_at

**Sample Response:**
```json
{
  "device_id": "abc123...",
  "activations": [{
    "license_key": "AFK-PRO-XXXXXXXX",
    "tier": "pro",
    "expires_at": "2026-04-04T10:35:00Z",
    "activated_at": "2026-01-04T10:36:00Z",
    "devices_max": 2,
    "devices_used": 1,
    "status": "active"
  }]
}
```

---

## 3) GET /api/devices/list ✅ PASS

**Logic Check:**
- Returns: device_id, alias (device_alias), last_seen (activated_at)
- With device_id: shows devices on same licenses as caller
- Without device_id: shows all devices (admin mode)

**Sample Response:**
```json
{
  "devices": [{
    "device_id": "abc123...",
    "alias": "Laptop Work",
    "last_seen": "2026-01-04T12:00:00Z"
  }]
}
```

---

## 4) DELETE /api/license/device/{id}/clear ✅ PASS

**Logic Check:**
- Requires: license_key query param
- Action: DELETE FROM license_devices
- Returns updated devices_used count (proves slot freed)
- No side effects on other data

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

---

## 5) GET /public/regions ✅ PASS

**Logic Check:**
- Returns SERVER_REGIONS list with display_name
- display_name: "Vietnam (Default)" - NOT "Unknown"
- Sorted by sort_order

**Sample Response:**
```json
{
  "regions": [{
    "id": "default",
    "display_name": "Vietnam (Default)",
    "id_server": "id.afkzone.cloud",
    "relay_server": "id.afkzone.cloud",
    "key": "EXOW136uTrC0PYYrkavoJH7SjkFlzPjB+vzzpvjsybw=",
    "enabled": true,
    "sort_order": 0
  }]
}
```

---

## 6) Renewal Logic ✅ PASS

**Logic Check:**
- /api/license/assign endpoint requires MANUAL call by UI
- Backend creates new license on different-tier renewal
- No auto-activate code path exists
- Device assignment only via explicit /api/license/assign call

**Verification:**
- Searched for "auto-activate" → not found
- Searched for "new_tier" → not found
- Renewal creates license, does NOT insert into license_devices

---

## Side Effects Check ✅ NO SIDE EFFECTS

| Endpoint | Side Effect | Status |
|----------|-------------|--------|
| purchase-history | READ only | ✅ Safe |
| activation-history | READ only | ✅ Safe |
| devices/list | READ only | ✅ Safe |
| clear slot | DELETE row | ✅ Expected |
| regions | READ only | ✅ Safe |

---

## Summary

| # | Endpoint | Status |
|---|----------|--------|
| 1 | /user/purchase-history | ✅ PASS |
| 2 | /user/activation-history | ✅ PASS |
| 3 | /api/devices/list | ✅ PASS |
| 4 | /api/license/device/{id}/clear | ✅ PASS |
| 5 | /public/regions | ✅ PASS |
| 6 | Renewal logic | ✅ PASS |

**READY FOR DEPLOY: YES**
