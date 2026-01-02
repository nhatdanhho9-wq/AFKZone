# Codebase Audit Report (No Changes Applied)

Date: 2026-01-01
Owner: Codex Team
Scope: Server + Flutter license/payment flows

## Findings (ordered by severity)

### Critical
1) Webhook signature bypass enabled in production
   - `DEV_BYPASS_SIGNATURE = True` accepts any request that includes `x-casso-signature`.
   - Impact: webhook authentication is effectively disabled.
   - File: `server_app.py` (around the `/payment/bank/webhook` handler).

### High
2) Trial filtering does not work (trials treated as paid)
   - `/user/history` filters by `tier == 'trial'` or `source == 'trial'`, but trials are stored with `tier = 'basic'` and `is_trial = TRUE`.
   - Client splits paid/trial using the same incorrect rule.
   - Impact: trial history appears in paid list; UI logic is misleading.
   - Files:
     - `server_app.py` (`/user/history` filtering)
     - `flutter/lib/mobile/pages/license_page.dart` (history split)

3) Device fingerprint still unstable
   - Uses `androidInfo.id` (Build.ID) and combines it with UUID; if Build.ID changes, fingerprint changes even though UUID is stable.
   - Impact: trial duplication, history mismatch after updates/reinstall.
   - File: `flutter/lib/common/license_service.dart` (`getDeviceFingerprint`)

### Medium
4) Admin key endpoints still active (JWT-only policy not fully enforced)
   - `/generate` and `/list` still accept `ADMIN_KEY`.
   - Impact: policy inconsistency, potential attack surface.
   - File: `server_app.py`

### Low
5) Duplicate dirty-flag check
   - `_checkDirtyFlag()` called twice in `initState`, redundant but harmless.
   - File: `flutter/lib/mobile/pages/license_page.dart`

6) Webhook payload logging may leak data
   - Logs up to 500 chars of payload; could include PII.
   - File: `server_app.py` (`/payment/bank/webhook`)

## Not verified
- APK build + runtime tests not completed (CI/tag build pending).
- No automated test suite executed.

## Recommended Next Actions
1) Disable DEV_BYPASS_SIGNATURE for production.
2) Add `is_trial` to `/user/history` response and use it for filtering on client.
3) Use `androidId` (or persistent UUID only) for fingerprint stability.
4) Decide whether admin_key endpoints should be removed or secured via JWT.

## Sign-off
Codex Team - 2026-01-01
