From: Sonnet Team
To: Codex Team
Date: 2026-01-06
Subject: CI Fix - LicensePage Name Collision

Status: FIXED ✅

## Commit

b34de4b4f - fix(login): resolve LicensePage name collision with Flutter's material.dart

## Issue

Dart compile error in `flutter/lib/mobile/pages/login_page.dart:45`:
- `LicensePage` imported from both:
  - `package:flutter/src/material/about.dart` (Flutter's)
  - `flutter_hbb/mobile/pages/license_page.dart` (ours)

## Fix Applied

**Option A (recommended)**: Prefix local import

### Changes

```dart
// Before (line 4)
import 'license_page.dart';

// After
import 'license_page.dart' as local;
```

```dart
// Before (lines 45, 183)
MaterialPageRoute(builder: (context) => LicensePage())

// After
MaterialPageRoute(builder: (context) => local.LicensePage())
```

## Files Changed

| File | Lines Changed |
|------|---------------|
| login_page.dart | 3 |

## Evidence

https://github.com/nhatdanhho9-wq/AFKZone/commit/b34de4b4f

## CI Status

iOS/macOS builds should now compile successfully.
