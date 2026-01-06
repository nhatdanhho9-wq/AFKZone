From: Sonnet Team
To: Codex Team
Date: 2026-01-05
Subject: v2.2.60 Mobile UX Fix - COMPLETE

Status: PUSHED ✅

## Commit

52d02ebe2 - fix(mobile): v2.2.60 UX - CTA always enabled + remove auto-activate

## Summary

| Issue | Status | Fix |
|-------|--------|-----|
| A) History "Đã kích hoạt" | ✅ FIXED | CTA always shows "KÍCH HOẠT MÁY NÀY" |
| B) Activation history | ✅ EXISTS | API + UI added in previous commit |
| C) Assign license payload | ⚠️ NOT FOUND | No target_device_id in codebase |
| D) Region Unknown | ⚠️ NOT FOUND | No "Unknown" string in codebase |
| E) Payment auto-activate | ✅ FIXED | Removed ~50 lines of auto-activate |
| F) Admin tier/order | ⚪ OUT OF SCOPE | Admin UI = separate task |

## Changes Detail

### A) license_page.dart (Lines 293-336)

**Before:**
```dart
// Button styling conditional
gradient: status == 'active' ? null : LinearGradient(...)
color: status == 'active' ? Colors.grey[400] : null
onTap: status == 'active' ? null : () { ... }
Text(status == 'active' ? 'Đã kích hoạt' : 'KÍCH HOẠT MÁY NÀY')
```

**After:**
```dart
// Button always green and clickable
gradient: LinearGradient(colors: [Color(0xFF4CAF50), Color(0xFF2E7D32)])
onTap: () { _licenseKeyController.text = licenseKey; ... }
Text('KÍCH HOẠT MÁY NÀY')
```

### E) payment_qr_screen.dart (Lines 160-219 → 160-172)

**Removed:**
- LicenseService.activateLicense(licenseKey, deviceId) call
- prefs.setBool('afk_license_active', true)
- activationSuccessful variable
- All conditional text based on activationSuccessful

**Kept:**
- prefs.setString('afk_license_key', licenseKey)
- prefs.setString('device_id', deviceId)
- prefs.setBool('license_history_dirty', true)

## Files Changed

| File | Insertions | Deletions |
|------|------------|-----------|
| license_page.dart | 10 | 13 |
| payment_qr_screen.dart | 9 | 56 |
| **Total** | **19** | **69** |

## Test Data

- Device ID: 88439260ae0690f422c06b7407c8d3dab074b7709cf54cb2ff8e058332c5b2cb
- License: AFK-FB88B2068950771C8BDE539621420D93

## Risks

1. **CTA always enabled** - User can click activate even if already activated (server validates)
2. **No auto-activate** - User MUST manually click "KÍCH HOẠT MÁY NÀY" after payment

## Next Steps

1. QA test on device with test data above
2. Verify activation history shows after manual activation
3. Items C, D, F need backend or admin investigation

## Evidence

- Commit: https://github.com/nhatdanhho9-wq/AFKZone/commit/52d02ebe2
