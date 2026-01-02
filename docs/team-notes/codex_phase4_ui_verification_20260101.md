# Phase 4 UI Fixes - Verification and APK Build

Date: 2026-01-01
Owner: Codex Team
Audience: Opus Team (implementation)

## Key Decision
Client UI changes require a new APK build. Existing installed apps will not update automatically.

## Required Actions
1) Build a new APK/IPA (release or debug for testing).
2) Bump versionCode/versionName to avoid stale installs.
3) Install the new build on device (uninstall old app or clear app data).

## Verification Steps
1) Create a paid order and complete QR payment.
2) Success dialog text must be readable (light theme applied).
3) Return to License page:
   - Purchase history should refresh and include the paid license.
4) Verify API:
   - `/user/history?device_id=...` returns the paid license.

## Pending Items to Finish
- 4.2 Server history check:
  - Ensure `bank_orders.device_id` matches the device fingerprint used by the client.
  - Ensure `license_devices` has a row for the paid license.
- 4.4 Show active license from local storage:
  - If history is empty, show the current license stored in SharedPreferences.

## Report Back
Please report:
- APK version used for testing.
- Screenshots of success dialog and history list.
- `/user/history` response for the test device.

## Sign-off
Codex Team - 2026-01-01
