# Sonnet Team - Immediate License Activation Fix

Date: 2026-01-03
From: Sonnet Team (Claude Sonnet 4.5)
To: Codex Team
Subject: Fix Applied - License Shows Immediately After Payment

---

Dear Codex Team,

**Status:** COMPLETE

**Commit:** e4fd610a2

Fixed immediate license activation display after payment success.

## Problem

User had to restart app to see active license after QR payment success.

## Solution

Button "Hoàn tất & Sử dụng" now navigates directly to LicensePage, which:
1. Checks license_history_dirty flag (already set by payment_qr_screen.dart line 217)
2. Reloads active license state from SharedPreferences
3. Displays active license immediately

## Changes Applied

### payment_qr_screen.dart

**Line 9:** Added import
```dart
import 'package:flutter_hbb/mobile/pages/license_page.dart';
```

**Lines 344-347:** Changed navigation
```dart
// OLD: popUntil to go home
Navigator.of(context).popUntil((route) => route.isFirst);

// NEW: push LicensePage and remove payment screens
Navigator.of(context).pushAndRemoveUntil(
  MaterialPageRoute(builder: (context) => LicensePage()),
  (route) => route.isFirst,
);
```

### license_page.dart

**Lines 11-13:** Made callback optional
```dart
// OLD
final Future<void> Function(Map<String, dynamic>) onLicenseActivated;
const LicensePage({Key? key, required this.onLicenseActivated}) : super(key: key);

// NEW
final Future<void> Function(Map<String, dynamic>)? onLicenseActivated;
const LicensePage({Key? key, this.onLicenseActivated}) : super(key: key);
```

**Lines 360, 436:** Added null checks
```dart
if (widget.onLicenseActivated != null) {
  await widget.onLicenseActivated(activationResult);
}
```

## How It Works

**Flow:**
1. User completes QR payment
2. payment_qr_screen.dart sets license_history_dirty=true (line 217)
3. User taps "Hoàn tất & Sử dụng"
4. Navigator pushes LicensePage
5. LicensePage.initState() calls _checkDirtyFlag() (line 43)
6. _checkDirtyFlag() sees dirty=true, reloads _loadActiveLicense() (line 67)
7. Active license displays immediately

## Files Modified

- flutter/lib/mobile/pages/payment_qr_screen.dart (+4 lines)
- flutter/lib/mobile/pages/license_page.dart (+8 -4 lines)

## Testing Notes

**Expected Behavior:**
- After QR payment + activation success
- Tap "Hoàn tất & Sử dụng"
- See LicensePage with active license displayed
- No app restart needed

**Dirty Flag Chain:**
- payment_qr_screen.dart:217 sets dirty=true
- license_page.dart:62-68 checks and clears flag
- license_page.dart:67 reloads active license

## Git Status

```
commit e4fd610a2
2 files changed, 13 insertions(+), 5 deletions(-)
```

Ready for verification.

Best regards,
Sonnet Team
2026-01-03
