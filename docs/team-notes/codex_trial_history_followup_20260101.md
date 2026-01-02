# Trial + History Follow-up (UI and Device Fingerprint)

Date: 2026-01-01
Owner: Codex Team
Audience: Opus Team (implementation)

## Findings
- Trial limits are enforced by `trial_devices.device_fingerprint`.
- Multiple trial licenses can appear if the device fingerprint changes (e.g., Build.ID changes on Android, app reinstall, or older builds used different fingerprint logic).
- Expired licenses are not auto-deleted; they are shown as history (limit 20).

## Required Fixes

### 1) Stabilize device fingerprint
Goal: One device equals one fingerprint across app updates.

Client change (recommended):
- Use Android `androidId` (not `androidInfo.id`) as the primary identifier.
- Fallback to a locally stored UUID (SharedPreferences) if `androidId` is null.
- Keep iOS `identifierForVendor` as primary.

Files:
- `flutter/lib/common/license_service.dart` (`getDeviceFingerprint`)

### 2) UI: History display behavior
Goal: Reduce confusion and noise in the license list.

Options (pick one, default recommended):
A) Default hide trials and expired items.
B) Split into sections: "Active/Paid" and "Trials/Expired" (collapsed).

Files:
- `flutter/lib/mobile/pages/license_page.dart`

### 3) Server: Optional filtering
Goal: Allow client to request only paid or only active licenses.

Add optional query params to `/user/history`:
- `include_trial` (default false)
- `include_expired` (default false)

Server file:
- `server_app.py` (`/user/history`)

## Verification
- Device gets only one trial even after app update/reinstall.
- History list shows paid license(s) clearly.
- Expired/trial items do not clutter the main list.

## Sign-off
Codex Team - 2026-01-01
