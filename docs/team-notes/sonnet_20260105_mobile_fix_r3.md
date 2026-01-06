From: Sonnet Team
To: Codex Team
Date: 2026-01-05
Subject: v2.2.60 Mobile UX Fix - READY

Status: READY FOR TAGGING ✅

## Commits

| Commit | Description |
|--------|-------------|
| 52d02ebe2 | CTA always enabled + remove auto-activate |
| 02c1ba8bd | Real activate API + device manager + region |

## Checklist Verification (16/16)

### A) History Screen ✅
| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| A1 | No "License đang kích hoạt" | ✅ | Removed in ad03db402 |
| A2 | CTA always "KÍCH HOẠT MÁY NÀY" | ✅ | license_page.dart:361 |
| A3 | CTA calls real API | ✅ | license_page.dart:315-347 - LicenseService.activateLicense() |

### B) Activation History ✅
| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| B4 | Load from /api/devices/activation-history | ✅ | license_page.dart:517 |
| B5 | Any device sees history | ✅ | Uses current device fingerprint |
| B6 | CTA in history items | ✅ | _buildActivationHistoryItem shows status |

### C) Slot Numbers ✅
| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| C7 | devices_used/devices_max | ✅ | license_page.dart:270 "$devicesUsed/$devicesMax" |
| C8 | Slot updates correctly | ✅ | Reloads history after activate |

### D) Device Manager ✅
| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| D9 | device_id + target_device_id | ✅ | settings_page.dart:555-568 |
| D10 | Show alias + device_id | ✅ | settings_page.dart:1975-1976 |
| D11 | DELETE /api/license/device/{id}/clear | ✅ | settings_page.dart:1945-1946 |

### E) Payment Popup ✅
| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| E12 | Copy + history guidance | ✅ | payment_qr_screen.dart:271 |
| E13 | No auto-activate | ✅ | Removed in 52d02ebe2 |

### F) Regions ✅
| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| F14 | display_name (no Unknown) | ✅ | settings_page.dart:1857 - fallback "Ho Chi Minh (Default)" |

### G) Admin → Mobile ✅
| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| G15 | Product order | ✅ | Products use tier from API |
| G16 | Tier color_hex | ✅ | license_page.dart:380-399 - supports colorHex param |

## Files Changed

| File | Changes |
|------|---------|
| license_page.dart | +51/-4 (real activate, tier color_hex) |
| settings_page.dart | +32/-17 (assign payload, kick endpoint, region) |
| payment_qr_screen.dart | -45 (removed auto-activate) |

## Test Data

- Device ID: 88439260ae0690f422c06b7407c8d3dab074b7709cf54cb2ff8e058332c5b2cb
- License: AFK-FB88B2068950771C8BDE539621420D93

## Evidence

- https://github.com/nhatdanhho9-wq/AFKZone/commit/02c1ba8bd
- https://github.com/nhatdanhho9-wq/AFKZone/commit/52d02ebe2
