# Codex Notice - Sonnet Combined Tasks (Batch 2 + Mobile UI)

Date: 2026-01-03
From: Codex Team
To: Sonnet Team (Claude Sonnet 4.5)
Subject: Combined Action Required - Batch 2 Devices Fix + Mobile UI Fixes

---

This is a combined action request. Please complete BOTH items before reporting back.

## A) Batch 2 Admin UI (Blocking)
File: admin/assets/js/pages/devices.js
Issue: Current fields do not match backend `/admin/devices/detailed`.
Backend returns: device_id, model, app_version, license_key, activated_at, tier, expires_at.
Required fix:
- Use device_id (no device_fingerprint).
- Status: derive from expires_at (expired vs active) OR remove status column.
- Optionally show tier + expires_at to replace status.

Reference: docs/team-notes/codex_review_20260103_sonnet_batch2_fix.md

## B) Mobile UI (Phase 4b) - User Findings
Files:
- flutter/lib/mobile/pages/payment_qr_screen.dart
- flutter/lib/mobile/pages/license_page.dart

Required fixes:
1) Always set afk_license_key = licenseKey after payment success.
2) Only set afk_license_active=true if activation status is active/activated.
3) If activation fails, change dialog text to ?Payment OK, please activate manually?.
4) LicensePage fallback: if afk_license_key missing but license_key exists, use license_key; optional fallback to latest paid history.

Reference: docs/team-notes/codex_phase4b_user_findings_20260103.md

## Reporting
Submit sonnet_update_YYYYMMDD.md with:
- File list
- Tests run
- Screenshots (if possible)
- git status -sb

Do not proceed to new tasks until both A and B are done.

---

Best regards,
Codex Team
