# CI v2.2.50 Failure Report

**From**: Opus Team  
**To**: Codex Team  
**Date**: 2026-01-03 07:10 UTC+7

---

## CI Run Details

| Field | Value |
|-------|-------|
| **Run URL** | [https://github.com/nhatdanhho9-wq/AFKZone/actions/runs/20661620641](https://github.com/nhatdanhho9-wq/AFKZone/actions/runs/20661620641) |
| **Tag** | v2.2.50 (commit `db0d6c488`) |
| **Duration** | 1h 10m 21s |
| **Status** | ❌ Failed |

---

## Failed Jobs Summary

| # | Job Name | Status |
|---|----------|--------|
| 1 | build rustdesk ios ipa (arm64-ios) | ❌ FAILED |
| 2 | x86_64-apple-darwin | ❌ FAILED |
| 3 | aarch64-apple-darwin | ❌ FAILED |
| 4 | Android APK aarch64 | ❌ FAILED |
| 5 | Android APK armv7 | ❌ FAILED |
| 6 | Android APK x86_64 | ❌ FAILED |
| 7 | Android APK universal | ❌ FAILED |
| 8 | x86_64-pc-windows-msvc | ❌ FAILED |
| 9 | x86_64-unknown-linux-gnu | ❌ FAILED |
| 10 | aarch64-unknown-linux-gnu | ❌ FAILED |

**Pattern**: All Flutter-based mobile/desktop builds failed. Non-Flutter jobs (Sciter, i686) passed.

---

## Error Analysis

### Error #1: Null-Safety Violation

**File**: `lib/mobile/pages/license_page.dart`  
**Line**: 398:46

**Error Excerpt**:
```
lib/mobile/pages/license_page.dart:398:46: Error: Can't use an expression 
of type 'Future<void> Function(Map<String, dynamic>)?' as a function 
because it's potentially null.
            await widget.onLicenseActivated(activationResult);
                                            ^
```

**Root Cause**: 
- `onLicenseActivated` callback is declared as nullable (`Function?`)
- Code calls it directly without null-check: `widget.onLicenseActivated(...)` 
- Dart null-safety requires explicit null-check before calling nullable functions

**Proposed Fix**:
```dart
// Before (line 398):
await widget.onLicenseActivated(activationResult);

// After:
await widget.onLicenseActivated?.call(activationResult);
```

---

### Error #2: Ambiguous Import

**File**: `lib/mobile/pages/payment_qr_screen.dart`  
**Line**: 346:57

**Error Excerpt**:
```
lib/mobile/pages/payment_qr_screen.dart:346:57: Error: 'LicensePage' is 
imported from both 'package:flutter/src/material/about.dart' and 
'package:flutter_hbb/mobile/pages/license_page.dart'.
            MaterialPageRoute(builder: (context) => LicensePage()),
                                                    ^^^^^^^^^^^
```

**Root Cause**:
- Flutter's `material.dart` exports a built-in `LicensePage` widget (for displaying OSS licenses)
- Project has custom `LicensePage` in `license_page.dart`
- Both are imported in `payment_qr_screen.dart` causing ambiguity

**Proposed Fix** (Option A - Hide Flutter's LicensePage):
```dart
// At imports in payment_qr_screen.dart:
import 'package:flutter/material.dart' hide LicensePage;
```

**Alternative Fix** (Option B - Rename custom widget):
```dart
// Rename custom widget to avoid collision:
class AppLicensePage extends StatefulWidget { ... }
```

---

## Summary Table

| Error | File | Line | Root Cause | Fix | Action |
|-------|------|------|------------|-----|--------|
| Null-safety | `license_page.dart` | 398 | Nullable callback invoked without null-check | `?.call()` | Code change |
| Ambiguous import | `payment_qr_screen.dart` | 346 | Name collision with Flutter's LicensePage | `hide LicensePage` | Code change |

---

## Next Steps

| Step | Action | Owner |
|------|--------|-------|
| 1 | Fix null-safety in `license_page.dart:398` | Sonnet Team |
| 2 | Fix ambiguous import in `payment_qr_screen.dart` | Sonnet Team |
| 3 | Push fix to `main` | Sonnet Team |
| 4 | Re-tag v2.2.51 or re-run v2.2.50 workflow | Codex Team |

**Recommendation**: **Code change required** before re-run. Re-running without fixes will produce the same errors.

---

**Sign-off**: Opus Team - 2026-01-03 07:10 UTC+7
