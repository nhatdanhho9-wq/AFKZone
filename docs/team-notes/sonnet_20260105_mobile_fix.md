From: Sonnet Team
To: Codex Team
Date: 2026-01-05
Subject: v2.2.59 Mobile UX Fix - PUSHED

Status: PUSHED ✅

## Commit

ad03db402 - v2.2.59 UX - activation history + remove active label

## Changes Summary

| Item | Status | Notes |
|------|--------|-------|
| A) Payment popup | ✅ Already done | "Vui lòng copy license key" (line 315) |
| B) History screen - no active label | ✅ FIXED | Removed "License đang kích hoạt:" section |
| C) Activation history API | ✅ ADDED | /api/devices/activation-history?device_id=xxx |
| D) Device manager | ✅ Already done | Settings with assign/kick |
| E) Regions | ✅ Already done | display_name fallback |
| F) Tier colors | ℹ️ Uses _getTierColor() | Hardcoded but visually distinct |

## File Changes

### license_page.dart (153+, 20-)

#### State Variables Added (lines 37-40)
```dart
bool _showActivationHistory = true;
List<Map<String, dynamic>> _activationHistory = [];
bool _activationHistoryLoading = true;
```

#### initState Updated (line 51)
```dart
_loadActivationHistory(); // NEW
```

#### _loadActivationHistory Method (lines 412-435)
- API: GET /api/devices/activation-history?device_id=xxx
- Uses LicenseService.getDeviceFingerprint()
- Parses activations/history array

#### _buildActivationHistoryItem (lines 367-413)
- Purple-themed card for each activation
- Shows tier, activated_at, license_key, status

#### _showAllActivationHistory (lines 415-432)
- Modal bottom sheet for full list

#### Activation History UI Section (lines 902-950)
- Collapsible header with count
- Loading state with CircularProgressIndicator
- Empty state with icon + message
- 3 items default + "Xem thêm" button

#### Removed Section (lines 847-864 → removed)
- "License đang kích hoạt:" label + item

## Test Case

Device ID: 680b8de740a1c5c452e90e3e5c1050c503dc6740f0bf90552c57f259acad7789

## Evidence

- Commit: https://github.com/nhatdanhho9-wq/AFKZone/commit/ad03db402
- Branch: main
