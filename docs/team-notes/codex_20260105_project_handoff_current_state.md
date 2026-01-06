# AFKZone Project Handoff (Current State)
Date: 2026-01-05  
Owner: Codex  

> Purpose: Snapshot “current state” used as the baseline for task assignment + review.
> This document intentionally **redacts credentials**. Refer to the secure channel for secrets.

---

## 1) Tổng quan dự án
- AFKZone là fork RustDesk + backend license/payment riêng (Casso).
- Mục tiêu: app remote desktop thương mại với quản lý license, lịch sử, thanh toán, admin dashboard.
- UI mobile + Admin dashboard đang được custom hoá mạnh.

## 2) Hạ tầng & URL
- API: `https://api.afkzone.cloud`
- Admin: `https://admin.afkzone.cloud`
- ID/Relay: `id.afkzone.cloud` (có kế hoạch multi‑region)
- Server Ubuntu: `172.26.31.115`, user `automation`, SSH key ở `C:\Users\admin\.ssh`
- Admin credential (prod): `admin / <redacted>` (kênh riêng)

## 3) Status hiện tại (Team)
- Opus: ĐANG LÀM (backend + deploy + CI/tag)
- Sonnet: ĐANG ĐỢI (chờ chỉ đạo tiếp; đã push UI fixes trước đó)
- OpusB: CI/infra (NASM mirror) đã xong; đang idle chờ lệnh
- OpusC: QA (mobile/admin) pending vì APK + credentials
- OpusD: Spot‑check code (r2 PASS)

## 4) Những quyết định/logic đã chốt
- Casso signature: strict, `DEV_BYPASS_SIGNATURE = False`.
- Product delete: nếu không có orders => hard delete; có orders => soft disable.
- Region switching: có popup cảnh báo “2 máy phải cùng server”.
- Renewal: hiện muốn bỏ (không auto‑extend).
- Assign license: yêu cầu loại bỏ, chỉ giữ “clear device”.
- Auto‑activate sau thanh toán: bỏ; user phải kích hoạt thủ công từ lịch sử.
- Admin dashboard phải là nguồn dữ liệu cho UI (CMS‑like).

## 5) Backend endpoints cần có (đã từng implement)
- GET `/user/purchase-history?device_id=xxx` (devices_used/max)
- GET `/user/activation-history?device_id=xxx`
- GET `/api/devices/list?device_id=xxx` (alias + last_seen)
- GET `/api/license/{key}/slots`
- DELETE `/api/license/device/{id}/clear`
- GET `/public/regions` (display_name)
- GET `/api/devices/activation-history?device_id=xxx` (alias endpoint)

## 6) Các bug/UX còn sai theo user test (v2.2.60)
- Payment popup: vẫn auto‑activate/logic sai. Phải chỉ hướng dẫn copy + kích hoạt ở lịch sử, button dẫn History.
- History after logout: đang hiển thị “Đã kích hoạt”; phải luôn có “KÍCH HOẠT MÁY NÀY” (clickable).
- Activation history trống trên máy phụ; mọi máy đã kích hoạt phải có history.
- Slot count (0/2, 0/5) sai → phải phản ánh thực tế.
- Device manager: clear device không hoạt động, thiếu alias.
- Region vẫn “Unknown” → phải hiển thị display_name từ `/public/regions`.
- Tier color: admin set màu nhưng mobile/ admin list không phản ánh.
- Product order: admin sort chưa phản ánh lên UI mobile.

## 7) CI / Tag
- Tag mới nhất: `v2.2.62` (commit `6ca6150d7` – “chore: bump version to 2.2.62+262”).
- CI run (theo handoff): `20718634738`.
- Lỗi CI trước đó do version mismatch đã fix (Cargo.toml).
- NASM mirror đã có: `https://github.com/nhatdanhho9-wq/nasm-mirror/releases/tag/v2.16.03`
  - SHA256: `0d29bcd8a5fc617333f4549c7c1f93d1866a4a0915c40359e0a8585bb1a5aa75`
  - Workflow update commit: `20a1718d6` (mirror URL)

## 8) Admin Dashboard status
- Login OK (prod credential in secure channel).
- Tabs pass QA (Licenses/Orders/Products/Tiers/Devices/Connections/Notifications/Analytics/Settings).
- Tier color UI có input nhưng hiển thị “No color” → cần fix.

## 9) Logo/Icon
- Sonnet đã replace toàn bộ icon sizes (Android/iOS/macOS/Windows) từ `AFKzonelogo.png`.
- macOS `.icns` verified (includes 1024).

## 10) Quy tắc vận hành team (rất quan trọng)
- Không giao việc song song khi 1 task chưa xong. Theo thứ tự: giao → nhận report → kiểm chứng → mới giao tiếp.
- Mọi report để trong `docs/team-notes/{team}_YYYYMMDD_*.md`
- Email giao việc phải rõ: “DO NOW” vs “WAIT”.
- Opus chỉ làm backend/CI/deploy; Sonnet chỉ làm `flutter/**` + `admin/**`.
- OpusB CI/infra; OpusC QA; OpusD spot‑check.

## 11) Task đang chờ (next actions)
- Ưu tiên: fix mobile UX theo yêu cầu user (manual activate only, history logic, activation history for all devices, slot count đúng, clear device + alias, region display_name).
- Sau khi fix: bump version + tag mới + CI → OpusC QA.
- Sau khi QA pass: đóng phase.

---

## Related evidence / reports (2026-01-05)
- `docs/team-notes/opus_20260105_admin_full_verify.md`
- `docs/team-notes/opus_20260105_ci_fail_summary.md`
- `docs/team-notes/opus_20260105_backend_fix.md`
- `docs/team-notes/sonnet_20260105_mobile_fix_r3.md`
- `docs/team-notes/opusc_20260105_qa_v2259.md`

