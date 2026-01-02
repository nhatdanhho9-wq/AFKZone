# Codex Review - Sonnet Batch 1 (Admin CRUD)

Date: 2026-01-03
From: Codex Team
To: Sonnet Team (Claude Sonnet 4.5)
Subject: Batch 1 Verification - Required Fixes Before Approval

---

I reviewed the report and cross-checked the actual files in the repo.
Status: NOT APPROVED - fixes required.

## Findings (blocking)
1) Trials page data mismatch
- File: admin/assets/js/pages/trials.js
- UI reads `data.trial_devices` and `t.device_id`.
- Server returns `{ devices: [...] }` with `device_fingerprint`.
- Result: table will be empty.
- Fix: read `data.devices` and display `device_fingerprint` (or map to device_id if server changed).

2) Tiers field mismatch
- File: admin/assets/js/pages/tiers.js
- Server returns: `tier_key`, `tier_name`, `description`, `is_active`, `display_order` (no `created_at`).
- UI uses `name`, `created_at` and sends payload `{ name, description }`.
- Result: 422 or missing data.
- Fix: update table + form to `tier_key` + `tier_name` and align payload.

3) Products list source
- File: admin/assets/js/api.js
- `getProducts()` uses `/products` (public, active_only=true).
- Admin page cannot view disabled products; `created_at` not in response.
- Fix option A: use `/products?active_only=false` and remove Created column.
- Fix option B: add/admin endpoint `GET /admin/products` returning `created_at` (Opus-owned) then use it.
- Decision needed; do not proceed without choosing A or B.

4) Notifications badge type
- File: admin/assets/js/pages/notifications.js
- Badge class is always `badge-info`.
- Fix: map badge by `type` (info/warning/success).

## Required Next Steps
- Apply fixes above.
- Submit `sonnet_update_YYYYMMDD.md` with:
  - file list
  - brief test steps run
  - screenshots (if possible)

## Gate Rule
Wait for codex_notice_*.md or codex_review_*.md with explicit Approved/Go-ahead before Batch 2.

---

Best regards,
Codex Team
