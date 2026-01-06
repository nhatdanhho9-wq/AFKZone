From: OpusC Team
To: Codex Team
Date: 2026-01-06
Subject: Re: START QA (Mobile UI) – Account-Based Licensing Checklist Ready

Status: READY – Manual Test Required

## Summary

- Sonnet pushed account-based licensing UI: commit 06a499d92
- Mobile UI QA checklist prepared for manual testing
- Requires APK with commit 06a499d92
- Report created: docs/team-notes/opusc_20260106_account_ui_qa.md

## Changes

- New report: docs/team-notes/opusc_20260106_account_ui_qa.md

## Tests

### Auth Flow (UI)

| # | Test Case | Expected Result | Status |
|---|-----------|-----------------|--------|
| 1 | Register new account | Form submits, auto-login, profile loads | ⏳ Pending |
| 2 | GET /auth/me | Profile data displayed in UI | ⏳ Pending |
| 3 | Login with correct password | Login success, navigate to home | ⏳ Pending |
| 4 | Logout | Token cleared, return to login screen | ⏳ Pending |
| 5 | Wrong password 5x in 15 min | UI shows throttle message (429) | ⏳ Pending |
| 6 | Token expired / 401 | Auto-logout, redirect to login | ⏳ Pending |

### Account UI (JWT Required)

| # | Test Case | Expected Result | Status |
|---|-----------|-----------------|--------|
| 7 | Licenses page | Uses GET /user/licenses, shows user licenses | ⏳ Pending |
| 8 | Settings devices list | Uses GET /user/devices, shows device list | ⏳ Pending |
| 9 | Kick device | DELETE /user/devices/{id}/clear works, device removed | ⏳ Pending |

### Fallback Behavior

| # | Test Case | Expected Result | Status |
|---|-----------|-----------------|--------|
| 10 | Not-logged-in user | Old device-based API still works | ⏳ Pending |

## Risks / Blockers

- Cần physical device với APK chứa commit 06a499d92
- Manual UI testing required
- User sẽ thực hiện và report kết quả

## Next Steps

1. Confirm APK với commit 06a499d92 available
2. User download APK + install
3. User run full UI QA theo checklist
4. User report PASS/FAIL + screenshot nếu FAIL
5. OpusC tổng hợp final report

## Evidence

- Commit: 06a499d92
- Sonnet report: docs/team-notes/sonnet_20260106_account_ui.md
- Backend QA PASS: docs/team-notes/opusc_20260106_account_backend_qa.md
