# Audit Follow-up Tasks + Overview

Date: 2026-01-01
Owner: Codex Team
Audience: Opus Team

## Overview (what is OK vs not OK)
OK:
- Core payment flow works (license issued after webhook).
- `/user/history` now joins `bank_orders` and supports filters.
- Client shows Active License + Paid/Trial sections (layout is in place).

NOT OK (must fix):
1) Webhook signature bypass enabled.
2) Trial filtering logic is incorrect.
3) Device fingerprint stability is not guaranteed.
4) Admin key endpoints still active (policy mismatch).
5) Minor cleanup: duplicate dirty flag check; noisy webhook logging.

## Task List (ordered by priority)

### T1 - Disable webhook bypass (Critical)
Files:
- `server_app.py` (`/payment/bank/webhook`)
Actions:
- Set `DEV_BYPASS_SIGNATURE = False` or remove bypass block.
- Keep strict signature verification (x-casso-signature or secure-token).
- Reduce payload logging to non-PII fields (trans_code, amount, tid).
Acceptance:
- Invalid signature → 401.
- Valid signature → 200.

### T2 - Fix trial filtering (High)
Files:
- `server_app.py` (`/user/history`)
- `flutter/lib/mobile/pages/license_page.dart`
Actions:
- In `/user/history`, include `is_trial` from `licenses.is_trial`.
- Apply filters using `is_trial`, not `tier == 'trial'`.
- Return `is_trial` in response.
- Client split: paid history = `is_trial == false`, trial history = `is_trial == true`.
Acceptance:
- Trial items no longer appear in paid list.

### T3 - Stabilize device fingerprint (High)
File:
- `flutter/lib/common/license_service.dart`
Actions:
- Use Android `androidId` as primary stable ID.
- If `androidId` is null, use persistent `device_uuid` only.
- Do not combine Build.ID (`androidInfo.id`) with UUID.
- Do not clear `device_uuid` on logout.
Acceptance:
- Same device gets one trial across app updates/reinstall.

### T4 - Admin auth cleanup (Medium)
File:
- `server_app.py`
Actions:
- Decide: remove admin_key endpoints (`/generate`, `/list`) or guard with JWT.
- Update docs to reflect JWT-only policy.
Acceptance:
- No admin_key-only endpoints remain in production.

### T5 - Minor cleanup (Low)
Files:
- `flutter/lib/mobile/pages/license_page.dart`
Actions:
- Remove duplicate `_checkDirtyFlag()` call.
Acceptance:
- No redundant calls in `initState`.

## Verification Plan
1) Build APK (CI tag build) and install.
2) Test payment flow + logout + history visibility.
3) Try trial twice (must fail on second attempt).
4) Capture screenshots + `/user/history` response.

## Sign-off
Codex Team - 2026-01-01
