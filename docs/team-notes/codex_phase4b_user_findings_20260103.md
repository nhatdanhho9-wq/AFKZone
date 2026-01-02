# Codex Findings - Phase 4b User UI Verification (v2.2.48)

Date: 2026-01-03
From: Codex Team
To: Opus Team + Sonnet Team
Subject: User UI Verification Notes (Screenshots Provided)

---

## Evidence Provided (User)
- Payment success dialog shows license key (visible and readable)
- Settings page shows Version 2.2.48
- Purchase history shows paid license entry
- Active license section shows "Unknown"

## Issues Observed
1) Active license shows "Unknown"
- Active card renders but license_key is missing in local state.
- Likely caused by missing prefs: afk_license_key not set when activation result lacks license_key.

2) Auto-activation claim vs actual state
- Success dialog states license auto-activated.
- User still must press Activate in License page.
- Indicates activation status not checked before showing "auto-activated" message.

3) Trial history toggle
- UI includes "Xem lich su dung thu (0)" collapse.
- This is for hiding trial entries; behavior is OK if no trials.

## Recommended Fixes (Client - Sonnet)
- PaymentQRScreen: only set afk_license_active=true if activation result status is active/activated.
- Always set afk_license_key=licenseKey on payment success (even if activation fails) so active card is not "Unknown".
- LicensePage: when afk_license_key missing but license_key exists, fallback to license_key; optionally fallback to latest paid history.
- Success dialog: if activation fails, change copy text to "Payment success - please activate manually".

## Optional Feature Request
Activation history (device list) requires new backend endpoint (e.g., license_devices list). If this adds complexity, skip.

---

Screenshots are available from user for Opus to attach to report.
