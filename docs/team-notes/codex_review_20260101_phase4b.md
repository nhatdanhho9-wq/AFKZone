# Codex Review - Phase 4b Status

Date: 2026-01-01
Owner: Codex Team
Audience: Opus Team

## Status
Pending verification (APK build + runtime tests required).

## What we accept as done
1) New APK built with updated fingerprint + UI changes.
2) History remains visible after logout (paid licenses still shown).
3) Trial appears once per device (stable fingerprint).
4) Paid history uses bank_orders and supports filters.

## Required Verification Steps
1) Build new APK and install (bump versionCode/versionName).
2) Run paid purchase flow:
   - Buy Basic and Enterprise on same device.
   - Confirm history shows both paid licenses.
3) Logout and re-open License page:
   - Active license card cleared.
   - Paid history still visible.
4) Trial check:
   - Try to generate trial twice on same device.
   - Second attempt must be blocked.
5) API check:
   - /user/history with include_trial=false, include_expired=false returns paid only.
   - /user/history with include_trial=true returns trial items.

## Request to Opus
Please send:
- APK version used for tests.
- Screenshots of License page after logout.
- /user/history response for the test device.

## Sign-off
Codex Team - 2026-01-01
