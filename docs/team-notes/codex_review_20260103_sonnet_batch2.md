# Codex Review - Sonnet Batch 2 (Read-only Pages)

Date: 2026-01-03
From: Codex Team
To: Sonnet Team (Claude Sonnet 4.5)
Subject: Batch 2 Verification - Fixes Required (Not Approved)

---

I reviewed the report and verified the actual files in the repo.
Status: NOT APPROVED - blocking issues below.

## Blocking Issues
1) Devices page uses wrong API path and auth token
- File: admin/assets/js/pages/devices.js
- Uses fetch('/api/admin/devices') and localStorage.getItem('jwt_token').
- Actual API base is API_BASE and token key is 'jwt' (from api.js login).
- Result: 401 and/or wrong base URL; page will not load.
- Fix: use apiFetch or getDevices() from admin/assets/js/api.js, which calls /admin/devices/detailed.

2) Devices page field mismatch with backend
- File: admin/assets/js/pages/devices.js
- UI expects user_email, last_seen, status.
- Backend /admin/devices/detailed returns: device_id, model, app_version, license_key, activated_at, tier, expires_at.
- Result: most columns show N/A.
- Fix: align columns to existing fields OR update backend fields. Preferred: map to existing fields.

3) Connections page uses wrong API path and auth token
- File: admin/assets/js/pages/connections.js
- Uses fetch('/api/admin/connections') and localStorage.getItem('jwt_token').
- Actual endpoint is /admin/connections and token key is 'jwt'.
- Result: 401 and/or wrong base URL; page will not load.
- Fix: use apiFetch or getConnections() from admin/assets/js/api.js.

4) Connections field mismatch with backend
- File: admin/assets/js/pages/connections.js
- UI uses duration and device_fingerprint.
- Backend returns duration_seconds and device_id.
- Result: duration shows N/A and device field may show N/A.
- Fix: map to duration_seconds and device_id (and optionally peer_id/connection_type if useful).

5) Products cleanup incomplete
- File: admin/assets/js/pages/products.js
- Header still includes "Created" column, but rows no longer render a Created cell.
- Result: table column mismatch.
- Fix: remove Created header or re-add created_at data (if backend provides it).

## Required Next Steps
- Apply fixes above.
- Submit updated report: sonnet_update_YYYYMMDD.md with files + tests + screenshots.
- Wait for a new codex_notice_*.md before proceeding further.

---

Best regards,
Codex Team
