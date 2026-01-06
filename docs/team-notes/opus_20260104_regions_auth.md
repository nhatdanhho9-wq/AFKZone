From: Opus Team
To: Codex Team
Date: 2026-01-04
Subject: v2.2.56 - Regions API Added + Auth Scheme Confirmed

Status: COMPLETE

## Summary

- Added GET /public/regions endpoint
- Documented auth scheme for all v2.2.56 endpoints
- Python syntax check: PASS
- Report: docs/team-notes/opus_20260104_regions_auth.md

## 1) Regions API - ADDED

- Endpoint: GET /public/regions
- Auth: NONE (public)
- Returns:
  - id, display_name, id_server, relay_server, key, enabled, sort_order
  - Currently has "Vietnam (Default)" region
  - Template for additional regions in code

## 2) Auth Scheme for New Endpoints

| Endpoint | Auth | Notes |
|----------|------|-------|
| /public/regions | NONE | Public, no auth |
| /user/purchase-history | device_id param | User endpoint, device_id acts as auth |
| /api/devices/list | device_id param | User endpoint, filters by device ownership |
| /api/license/assign | device_id in body | User endpoint, license_key + device_id combo |
| /api/license/{key}/slots | NONE | Public, license_key acts as auth |
| PATCH /api/license/device/{id}/alias | NONE | Public, device_id acts as auth |

## Changes

- server_app.py: Added SERVER_REGIONS config
- server_app.py: Added GET /public/regions endpoint
- server_app.py: Added auth documentation comments

## Tests

- Python syntax (py_compile): PASS

## Next Steps

- Codex approve Sonnet push
- Sonnet implement UI for regions, purchase history, assign

## Evidence

- /public/regions endpoint added
- Auth documented in code comments (lines 540-548)
