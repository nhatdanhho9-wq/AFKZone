# Phase 4b Full Task Plan - Trial + History + Logout UX

Date: 2026-01-01
Owner: Codex Team
Audience: Opus Team (implementation)

## Why license disappears after logout (current behavior)
- Logout removes the device from `license_devices` and clears local storage.
- `/user/history` currently returns licenses tied to the **current device**.
- Result: after logout, history list becomes empty even if a paid license exists.

## Phase 4b Goal
Keep paid licenses visible after logout, stop trial duplication, and clean up history UI.

## Server Tasks (Required)
1) Update `/user/history` query and response:
   - Inputs: `device_id`, `fingerprint`, `include_trial` (default false), `include_expired` (default false), `offset` (default 0), `limit` (default 20).
   - Data source:
     - Use `bank_orders` by `device_id` where status in (`success`, `completed`).
     - Join `licenses` by `license_key`.
   - Return fields per item:
     - `license_key`, `tier`, `duration_days`, `expires_at`, `status`, `paid_at`, `source`,
       `device_count`, `max_devices`.
   - Status rules:
     - `revoked` if `licenses.is_revoked` true.
     - `expired` if `expires_at < now`.
     - else `active`.
2) Keep device slot logic in `license_devices` only.
3) Leave `license/logout` behavior unchanged (logout removes device slot).

## Client Tasks (Required)
1) Stabilize device fingerprint in `flutter/lib/common/license_service.dart`:
   - Use Android `androidId` as primary identifier.
   - Store a persistent `device_uuid` in SharedPreferences on first run.
   - Compute fingerprint as SHA256 of `androidId` (or `device_uuid` if androidId is not available).
   - Do not delete `device_uuid` on logout.
2) License history UI in `flutter/lib/mobile/pages/license_page.dart`:
   - Add sections:
     - "Active license on this device" (from local storage).
     - "Paid licenses" (from `/user/history` default filters).
     - "Trials / Expired" collapsed (toggle to show).
   - Use `/user/history` filters to hide trial/expired by default.
3) After logout:
   - Clear local active license.
   - Keep history list visible (paid purchases remain).
4) After payment:
   - `license_history_dirty` already set in `payment_qr_screen.dart`.
   - Ensure license page reloads history when dirty flag is true (already implemented).

## Build + Release
1) Bump versionCode/versionName.
2) Build new APK and install for test.

## Verification Steps
1) Purchase Basic + Enterprise from one device.
2) Confirm history shows both paid licenses.
3) Logout on device:
   - Active license cleared locally.
   - History still shows paid licenses.
   - `device_count` decreases after logout.
4) Trial:
   - Only one trial ever allowed for the same device fingerprint.
5) UI:
   - Paid list is clean; trials/expired are hidden unless expanded.

## Deliverables
- Server: `server_app.py` updated `/user/history`.
- Client: `license_service.dart`, `license_page.dart`.
- New APK for testing.

## Sign-off
Codex Team - 2026-01-01
