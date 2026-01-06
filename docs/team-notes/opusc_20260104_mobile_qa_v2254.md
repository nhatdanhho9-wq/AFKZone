From: OpusC Team
To: Codex Team
Date: 2026-01-04
Subject: Mobile QA Checklist Ready – v2.2.54 APK

Status: READY FOR MANUAL TEST

## Summary

- APK v2.2.54 artifacts confirmed available at GitHub Actions
- Run FAIL (macOS jobs) nhưng Android APK artifacts usable
- Mobile QA test checklist created (8 test cases)
- /public/notifications đã test PASS trước đó (2 notifications)
- Admin QA: vẫn WAITING (chờ credentials)
- Report created: docs/team-notes/opusc_20260104_mobile_qa_v2254.md

## Changes

- Report: docs/team-notes/opusc_20260104_mobile_qa_v2254.md (mới tạo)

## Tests

| # | Test Case | Expected Result | Status |
|---|-----------|-----------------|--------|
| 1 | Install APK v2.2.54 | App installs successfully | ⏳ Pending |
| 2 | Version display | Shows 2.2.54+254 in Settings/About | ⏳ Pending |
| 3 | Open "Thông tin & Thông báo" | Screen loads | ⏳ Pending |
| 4 | Notifications display | Shows 2 notifications from /public/notifications | ⏳ Pending |
| 5 | Initiate payment | QR code displayed | ⏳ Pending |
| 6 | Complete payment | Success popup appears | ⏳ Pending |
| 7 | Click "Hoàn tất & Sử dụng" | Navigates to License Info screen | ⏳ Pending |
| 8 | License Info display | Shows license key, tier, expiry | ⏳ Pending |

## CI Run Links for QA

### v2.2.54 Tag Build (Artifacts Ready)
- URL: https://github.com/nhatdanhho9-wq/AFKZone/actions/runs/20674076171
- Artifacts:
  - aarch64 APK: https://github.com/nhatdanhho9-wq/AFKZone/actions/runs/20674076171/artifacts/5012962511
  - Universal APK: https://github.com/nhatdanhho9-wq/AFKZone/actions/runs/20674076171/artifacts/5012997621
- Note: Filenames show "2.0.5" but internal version IS 2.2.54+254

## Risks / Blockers

- Run FAIL có thể ảnh hưởng đến non-Android artifacts
- Cần device thật để test payment flow
- Admin credentials: Still pending from Codex

## Next Steps

- User download APK từ GitHub Actions artifacts
- User install + chạy manual test theo checklist
- User report kết quả từng test case
- OpusC tổng hợp kết quả vào final report
- Chờ Admin credentials để tiếp tục Admin QA

## Evidence

- /public/notifications: PASS (2 notifications returned)
- Artifacts URL confirmed: https://github.com/nhatdanhho9-wq/AFKZone/actions/runs/20674076171
- Multiple APK variants available (universal, aarch64, armv7, x86_64)
