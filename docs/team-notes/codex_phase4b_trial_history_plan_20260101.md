# Phase 4b Plan - Trial + History + Logout UX

Date: 2026-01-01
Owner: Codex Team
Audience: Opus Team (implementation)

## Scope
Fix trial duplication, clarify license history, and define logout behavior.

## Decisions (must follow)
1) "License of yours" shows paid purchases for this device even after logout.
2) Trials and expired licenses are hidden by default; user can expand to view.
3) History is device-based (no user accounts in this phase).

## Server Tasks
1) Extend `/user/history` to support filters:
   - `include_trial` default false
   - `include_expired` default false
2) Include paid purchases from `bank_orders` by `device_id`:
   - Join `bank_orders` -> `licenses` by `license_key`.
   - Return fields: `license_key`, `tier`, `duration_days`, `expires_at`, `status`, `paid_at`, `source`.
3) Keep limit 20, but allow `offset` for pagination.

## Device Count (critical rule)
- License slot usage is computed only from `license_devices`.
- History list must not affect slot counts.
- If UI needs device usage per license, fetch it from server (`/license/info`) or add `device_count` + `max_devices` to `/user/history` response.

## Client Tasks
1) Stabilize device fingerprint:
   - Use `androidId` as primary (fallback to `id`).
   - If missing, use a stored UUID in SharedPreferences.
   - Do not clear this UUID on logout.
2) License page UI:
   - Show "Active license on this device" from local storage (if exists).
   - Show "Paid licenses" list from `/user/history` (default filters).
   - Add a collapsed "Trials / Expired" section.
3) After logout:
   - Clear local active license info.
   - Keep history list available (paid purchases still visible).

## Verification
1) Trial can be generated only once per device.
2) Paid license stays visible in history after logout.
3) Default list is clean (no trial/expired clutter).
4) Optional: expand to view trial/expired items.

## Deliverables
- Server patch: `server_app.py`
- Client patch: `flutter/lib/common/license_service.dart`, `flutter/lib/mobile/pages/license_page.dart`
- New APK for test and release

## Sign-off
Codex Team - 2026-01-01
