# UI Follow-up: License List + Payment Success Dialog

Date: 2026-01-01
Owner: Codex Team
Audience: Opus Team (implementation)

## Context
- Payment webhook now works and license is issued.
- User sees only trial licenses in "License of yours" list.
- Payment success dialog text is hard to read (low contrast).

## Expected Behavior
- The license list should show the latest paid license for the current device.
- Success dialog text should be readable in dark theme.

## Required Fixes

### 1) License list refresh after payment
Goal: After a successful payment, the license list must reload and show the paid license.

Implementation (do this exact flow):
1. In `flutter/lib/mobile/pages/payment_qr_screen.dart`, after payment success:
   - Set a shared flag: `prefs.setBool('license_history_dirty', true)`.
2. In `flutter/lib/mobile/pages/license_page.dart`:
   - On `initState` and on page resume, check `license_history_dirty`.
   - If true, call `_loadPurchaseHistory()` and clear the flag.

Notes:
- This avoids dependency on navigation return results because the success flow uses `popUntil`.

### 2) Ensure server history includes paid license
Goal: `/user/history` should return the paid license for the device.

Checks:
- Verify `bank_orders.device_id` equals the device fingerprint used on the client.
- Verify a row exists in `license_devices` for that `license_key`.
- If missing, insert after webhook success.

SQL quick checks (reference only):
```
SELECT trans_code, device_id, license_key, status FROM bank_orders WHERE trans_code = :code;
SELECT * FROM license_devices WHERE license_key = :license_key;
```

### 3) Success dialog readability (dark theme)
Goal: Text in the success dialog must be readable.

Implementation:
- Set explicit text color for all labels inside the success dialog:
  - Use `Colors.black87` for text on light backgrounds.
- Set `AlertDialog` background to white, or wrap in `Theme(data: ThemeData.light())`.
- Set license key text color explicitly (monospace + `Colors.black87`).

Files:
- `flutter/lib/mobile/pages/payment_qr_screen.dart` (success dialog)

### 4) Optional: show current active license
Goal: If history is empty, still show the currently active license from local storage.

Implementation:
- Read `license_key` and `afk_license_expires_at` from SharedPreferences.
- Render a "Current License" card above the history list.

## Verification Checklist
- After payment, "License of yours" list shows the new paid license.
- `/user/history?device_id=...` returns the paid license.
- Success dialog text is clearly readable on dark theme.

## Sign-off
Codex Team - 2026-01-01
