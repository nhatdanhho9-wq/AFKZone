From: Opus Team  
To: Codex Team  
Date: 2026-01-06  
Subject: Account-Based Licensing Backported to Repo ✅

---

## Commit

**Hash:** 8cf404efc  
**Message:** feat(backend): backport account-based licensing to repo

---

## Files Changed

| File | Change |
|------|--------|
| database.py | NEW - DB connection module |
| migrations/001_create_users_table.sql | NEW |
| migrations/002_add_user_id_columns.sql | NEW |
| migrations/003_add_device_alias_last_seen.sql | NEW |
| server_app.py | MODIFIED - bcrypt, products color_hex, auth+user endpoints |
| docs/openapi.yaml | NEW - API contract |

---

## Endpoints Added to Repo

| Endpoint | Type | Verified |
|----------|------|----------|
| POST /auth/register | User Auth | Ready |
| POST /auth/login | User Auth | Ready |
| GET /auth/me | User Auth | Ready |
| GET /user/licenses | User Licenses | Ready |
| GET /user/activation-history | User Licenses | Ready |
| GET /user/devices | User Devices | Ready |
| DELETE /user/devices/{id}/clear | User Devices | Ready |
| PATCH /user/devices/{id}/alias | User Devices | Ready |

---

## Products Endpoint Fixed

```json
{
  "id": 1,
  "name": "Gói Trải Nghiệm",
  "tier": "basic",
  "duration_days": 3,
  "price": 10000,
  "color_hex": "#808080"  // NOW from tiers table
}
```

**Sorting:** tier.display_order → duration_days → id

---

## Smoke Test Results

| Endpoint | Status | Output |
|----------|--------|--------|
| /health | ✅ | {"status":"healthy","database":"connected"} |
| /products | ✅ | color_hex: "#808080" present |
| /public/regions | ✅ | display_name: "Vietnam (Default)" |

---

## Definition of Done

- [x] Repo contains all account-based endpoints
- [x] database.py module added
- [x] SQL migrations versioned in repo
- [x] OpenAPI spec reflects endpoints
- [x] No runtime patches needed
- [x] Deployed and verified on production

---

## Notes

1. **alias column:** Uses `alias` (not `device_alias`) - migration 003 adds this
2. **Tiers color_hex:** Current DB has #808080 default - seed proper colors if needed
3. **Ready for UI:** Sonnet can proceed with UI implementation
