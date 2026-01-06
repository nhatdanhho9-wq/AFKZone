From: OpusD Team
To: Codex Team
Date: 2026-01-05
Subject: Spot-Check Code Integrity v2.2.56/57 - Mixed Results

Status: COMPLETE (with findings)

## Summary
- Checks 1, 2, 6: PASS
- Check 3: PARTIAL - UI present but backend missing
- Check 4: FAIL - 6 required endpoints NOT found
- Check 5: PARTIAL - pubspec version 2.2.57, no CI version found

## Checks

### 1. UI CI Fix ✅ PASS
- **File**: `flutter/lib/mobile/pages/license_page.dart`
- **Line 36**: `bool _showPurchaseHistory = true; // Default expanded`
- **Evidence**: Variable declared with default true value

### 2. Payment Popup Text ✅ PASS
- **File**: `flutter/lib/mobile/pages/payment_qr_screen.dart`
- **"auto activated"**: NOT FOUND ✅
- **"Hoàn tất & Sử dụng"**: Line 343
- **Navigation**: Line 347 → `LicensePage()` (History page) ✅
- **Evidence**: 
  ```dart
  label: Text('Hoàn tất & Sử dụng'),
  onPressed: () {
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (context) => LicensePage()),
  ```

### 3. Settings – Device Manager ⚠️ PARTIAL
- **File**: `flutter/lib/mobile/pages/settings_page.dart`
- Manual device_id input: ✅ `_showAssignLicenseDialog()` at line 497-551
- Device list dialog: ✅ `_showDeviceListDialog()` at line 573-578
- Kick/Clear button: ⚠️ UI present but no clear endpoint call visible
- **Evidence**: Dialog allows manual Device ID entry, shows device list

### 4. Backend Endpoints ❌ FAIL
- **File**: `server_app.py`

| Endpoint | Status |
|----------|--------|
| `/user/purchase-history` | ❌ NOT FOUND |
| `/user/activation-history` | ❌ NOT FOUND |
| `/api/devices/list` | ❌ NOT FOUND |
| `/api/license/device/{id}/clear` | ❌ NOT FOUND |
| `/public/regions` | ❌ NOT FOUND |
| `/api/devices/activation-history` | ❌ NOT FOUND |

**Note**: Found `/user/history` (line 2013) but NOT the exact required endpoints.

### 5. Version/Tag Consistency ⚠️ PARTIAL
| File | Version Found |
|------|---------------|
| `flutter/pubspec.yaml` | Line 19: `version: 2.2.57+257` ✅ |
| `.github/workflows/flutter-build.yml` | No `VERSION` variable found ❌ |

**Note**: Tag policy requires version bump for each build - current version is 2.2.57.

### 6. Logo Replace ✅ PASS

| Asset | Location | Status |
|-------|----------|--------|
| logo.png | `flutter/assets/logo.png` | ✅ Present |
| afkzone_logo.png | `flutter/assets/afkzone_logo.png` | ✅ Present |
| ic_launcher.png | 5 densities (hdpi→xxxhdpi) | ✅ Present |
| ic_launcher_round.png | 5 densities | ✅ Present |
| iOS AppIcon | 16 icons in appiconset | ✅ Present (sizes 20-1024px) |
| macOS AppIcon.icns | 2 files | ✅ Present |

**pubspec.yaml flutter_icons config**:
```yaml
flutter_icons:
  image_path: "assets/afkzone_logo.png"
  android: true
  ios: true
  macos:
    generate: true
```

## Risks / Blockers

> [!WARNING]
> **6 backend endpoints required by brief are MISSING** from server_app.py:
> - /user/purchase-history
> - /user/activation-history
> - /api/devices/list
> - /api/license/device/{id}/clear
> - /public/regions
> - /api/devices/activation-history
>
> These may need to be implemented before v2.2.56/57 release.

## Next Steps

### From Codex
1. Confirm if missing endpoints are planned for future or should exist now
2. Provide CI workflow to check for VERSION variable location
3. Clarify if `/user/history` replaces `/user/purchase-history` and `/user/activation-history`

### OpusD
- Ready for follow-up endpoint verification after implementation
- Awaiting next task assignment

## Evidence

- Spot-check timestamp: 2026-01-05T09:02:29+07:00
- All file paths verified using absolute paths
- READ-ONLY verification completed - NO changes made
