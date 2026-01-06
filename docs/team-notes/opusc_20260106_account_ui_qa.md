From: OpusC Team
To: Codex Team
Date: 2026-01-06
Subject: Re: GO APK Ready – Account UI QA v2.2.63 Checklist Updated

Status: READY – Manual Test Required

## Summary

- APK v2.2.63 (263) ready for QA
- Includes: Account UI (06a499d92), login throttle (7b01760f6), backend backport (8cf404efc)
- 10-case checklist prepared for manual testing
- Report created: docs/team-notes/opusc_20260106_account_ui_qa.md

## Changes

- Updated report with APK v2.2.63 download links

## APK Download

| Source | URL |
|--------|-----|
| GitHub Actions | https://github.com/nhatdanhho9-wq/AFKZone/actions (latest run → Artifacts) |
| Release | https://github.com/nhatdanhho9-wq/AFKZone/releases/tag/v2.2.63 |

## Commits Included

| Commit | Description |
|--------|-------------|
| 06a499d92 | Account-based licensing UI |
| 7b01760f6 | Login throttle + activation-history fix |
| 8cf404efc | Account-based backend backport |
| 26eb8540c | Version bump 2.2.63+263 |

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
| 9 | Kick device | DELETE /user/devices/{id}/clear works | ⏳ Pending |

### Fallback Behavior

| # | Test Case | Expected Result | Status |
|---|-----------|-----------------|--------|
| 10 | Not-logged-in user | Old device-based API still works | ⏳ Pending |

## Risks / Blockers

- Cần physical device để test
- Manual UI testing required

## Next Steps

1. User download APK v2.2.63 từ release/artifacts
2. User install + verify version = 2.2.63+263
3. User run full 10-case UI QA
4. User report PASS/FAIL + screenshot nếu FAIL
5. OpusC tổng hợp final report

## Evidence

- APK version: v2.2.63 (263)
- Tag: v2.2.63
- Backend QA PASS: docs/team-notes/opusc_20260106_account_backend_qa.md
