From: Sonnet Team
To: Codex Team
Date: 2026-01-06
Subject: Account-Based Licensing UI - COMPLETE

Status: PUSHED ✅

## Commit

06a499d92 - feat(mobile): account-based licensing UI integration
(635 insertions, 19 deletions)

## New Files

| File | Description |
|------|-------------|
| auth_service.dart | JWT auth: register, login, logout, getMe, 429 handling |
| login_page.dart | Email/password form, throttle error display |
| register_page.dart | Registration with auto-login |

## Modified Files

| File | Changes |
|------|---------|
| license_page.dart | Use /user/licenses with JWT, fallback if not logged in |
| settings_page.dart | Use /user/devices and /user/devices/{id}/clear with JWT |

## Endpoints Integrated

Per docs/openapi.yaml v2.2.62:

| Endpoint | Method | Auth | Used In |
|----------|--------|------|---------|
| /auth/register | POST | - | AuthService.register() |
| /auth/login | POST | - | AuthService.login() |
| /auth/me | GET | JWT | AuthService.getMe() |
| /user/licenses | GET | JWT | license_page._loadPurchaseHistory() |
| /user/devices | GET | JWT | settings_page._loadDevices() |
| /user/devices/{id}/clear | DELETE | JWT | settings_page._kickDevice() |

## Features

1. **429 Throttle Handling**: "Quá nhiều lần thử. Vui lòng đợi 15 phút."
2. **401 Token Expired**: Auto-logout + show login
3. **Fallback**: Non-logged-in users use old device-based API

## Evidence

https://github.com/nhatdanhho9-wq/AFKZone/commit/06a499d92
