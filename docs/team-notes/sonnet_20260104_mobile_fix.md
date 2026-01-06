From: Sonnet Team
To: Codex Team
Date: 2026-01-04
Subject: PUSHED - v2.2.56 UX Fix - Payment Popup + Device Manager

Status: PUSHED ✅

## Summary

- Commit dadd7a9c5 pushed to origin/main
- 2 files changed, 213 insertions(+), 17 deletions(-)

## Commit Hash

- Full: dadd7a9c5
- Short: dadd7a9

## Changes

### B) Payment Popup
- ❌ Removed: "License đã được tự động kích hoạt trên thiết bị này"
- ✅ Added: "Vui lòng copy license key để lưu lại"
- ✅ Button always navigates to History (not LicenseInfoPage)
- ✅ Removed LicenseInfoPage import

### D) Device Manager in Settings
- ✅ New "Quản lý thiết bị" section (appears when license active)
- ✅ "Gán license cho thiết bị khác" - manual device_id input
- ✅ "Xem thiết bị đã kích hoạt" - device list with kick button
- ✅ API: GET /api/license/{key}/slots
- ✅ API: POST /api/license/kick

## Files Changed

 flutter/lib/mobile/pages/payment_qr_screen.dart | 25 +--
 flutter/lib/mobile/pages/settings_page.dart     | 205 +++++++++

## Tests

- Commit: SUCCESS ✅
- Push: SUCCESS ✅
- Build: Pending CI

## Risks / Blockers

- None

## Pending (cần QA test)

- A) History screen - đã có collapsible lists, cần verify
- E) Region switch - đã có API call, cần verify display_name
- G) Logo replace - cần manual copy AFKzonelogo.png

## Evidence

- GitHub: https://github.com/nhatdanhho9-wq/AFKZone/commit/dadd7a9c5
