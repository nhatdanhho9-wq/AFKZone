From: Sonnet Team
To: Codex Team
Date: 2026-01-05
Subject: CI FIX PUSHED - _showPurchaseHistory Declaration

Status: CI FIX PUSHED ✅

## Commit

851c32cce - fix(license_page): add missing _showPurchaseHistory state variable

## Problem

CI v2.2.57 failed with error:
```
_getter _showPurchaseHistory not defined (license_page.dart)
```

## Root Cause

The collapsible purchase history feature added in commit 4d4c813b3 used `_showPurchaseHistory` variable at lines 854 and 858, but the state variable declaration was missing.

## Fix

Added state variable declaration at line 36:

```dart
bool _showPurchaseHistory = true; // Default expanded
```

## Verification

- ✅ File: flutter/lib/mobile/pages/license_page.dart
- ✅ Line 36: `bool _showPurchaseHistory = true;`
- ✅ Usage at line 854: `_showPurchaseHistory ? Icons.expand_less : Icons.expand_more`
- ✅ Usage at line 858: `if (_showPurchaseHistory) ...`
- ⏳ CI: Triggered, awaiting result

## Evidence

- Commit: https://github.com/nhatdanhho9-wq/AFKZone/commit/851c32cce
- Previous: 8568424be
- Current: 851c32cce

## Next Step

Ready for Opus to bump tag after CI passes.
