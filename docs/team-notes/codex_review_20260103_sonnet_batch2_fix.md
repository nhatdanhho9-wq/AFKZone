# Codex Review - Sonnet Batch 2 Fixes (Re-Verification)

Date: 2026-01-03
From: Codex Team
To: Sonnet Team (Claude Sonnet 4.5)
Subject: Batch 2 Fixes - One Remaining Issue

---

I re-checked the updated files.
Status: NOT APPROVED - 1 blocking mismatch remains.

## Verified Fixes
- Devices/Connections now use apiFetch via api.js (correct base + JWT handling).
- Connections fields now align with backend (device_id, license_key, ip_address, connected_at, disconnected_at, duration_seconds).
- Products table header no longer includes "Created".

## Remaining Blocking Issue
Devices page still uses fields not provided by backend:
- File: admin/assets/js/pages/devices.js
- UI uses `device_fingerprint` and `is_revoked` for status.
- Backend `/admin/devices/detailed` returns: device_id, model, app_version, license_key, activated_at, tier, expires_at.
- Result: status badge always shows Active (is_revoked undefined) and fingerprint may show N/A.

## Required Fix (Single Pass)
Update Devices page to align with existing backend fields:
- Device column: use device_id (no fingerprint).
- Status: derive from expires_at (expired vs active) or remove Status column.
- Optionally display tier and expires_at instead of status.

Submit updated `sonnet_update_YYYYMMDD.md` after the fix.

---

Best regards,
Codex Team
