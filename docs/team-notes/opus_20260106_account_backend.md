From: Opus Team  
To: Codex Team  
Date: 2026-01-06  
Subject: Account-Based Licensing Backend - DONE ✅

---

## Summary

Backend account-based licensing MVP implemented and deployed to production.

---

## Database Changes

| Table | Column | Type | Status |
|-------|--------|------|--------|
| users | (new table) | - | ✅ Created |
| licenses | user_id | INTEGER FK | ✅ Added |
| bank_orders | user_id | INTEGER FK | ✅ Added |
| license_devices | alias | VARCHAR(255) | ✅ Added |
| license_devices | last_seen | TIMESTAMP | ✅ Added |

---

## New API Endpoints

### A. User Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/register | Register with email/password |
| POST | /auth/login | Login, returns JWT token |
| GET | /auth/me | Get current user info |

### B. User Licenses
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /user/licenses | List user's licenses with devices_used/max |

### C. Activation History
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /user/activation-history | Get activation history by device_id |

### D. Device Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /user/devices | List user's activated devices |
| DELETE | /user/devices/{id}/clear | Clear/kick device |
| PATCH | /user/devices/{id}/alias | Update device alias |

---

## Sample Responses

### GET /user/licenses
```json
{
  "licenses": [{
    "license_key": "AFK-xxx",
    "tier": "pro",
    "duration_days": 30,
    "expires_at": "2026-02-05T...",
    "status": "active",
    "devices_max": 5,
    "devices_used": 2,
    "created_at": "2026-01-06T..."
  }]
}
```

### GET /user/devices
```json
{
  "devices": [{
    "device_id": "abc123...",
    "alias": "iPhone 15",
    "last_seen": "2026-01-06T...",
    "activated_at": "2026-01-01T...",
    "license_key": "AFK-xxx",
    "tier": "pro"
  }]
}
```

### GET /user/activation-history
```json
{
  "device_id": "abc123...",
  "activations": [{
    "license_key": "AFK-xxx",
    "tier": "pro",
    "expires_at": "2026-02-05T...",
    "activated_at": "2026-01-01T...",
    "devices_max": 5,
    "devices_used": 2,
    "status": "active"
  }]
}
```

---

## Existing Endpoints Verified

| Endpoint | Status | Notes |
|----------|--------|-------|
| /public/regions | ✅ | display_name: "Vietnam (Default)" |
| /products | ✅ | Working (needs color_hex fix in future) |
| /health | ✅ | Healthy |

---

## Notes

1. **NO auto-activate**: Payment webhook creates license only, no device assignment
2. **User JWT**: Separate from admin JWT, 30-day expiry
3. **Products color_hex**: Still pending - current products endpoint works but doesn't include color_hex from tiers table

---

## Status: READY FOR UI

Sonnet can now begin UI implementation for account-based licensing.
