# Next Steps Plan - Phase 4b CI Build + Remaining Phases

Date: 2026-01-01
Owner: Codex Team
Audience: Opus Team (implementation)

## Workstream A - Phase 4b (Client Verification via CI)
Goal: Produce APK via GitHub Actions and verify the client changes.

### A1) Prepare release commit
1) Bump version in `flutter/pubspec.yaml`
   - Current: `2.2.28+228`
   - Example target: `2.2.46+246` (match server v2.2.46)
2) Ensure Phase 4b client changes are in the same commit.
3) Commit message:
   - `feat: phase4b client history + fingerprint`

### A2) Trigger CI APK build (same flow as before)
1) Push to main.
2) Create tag and push:
   - `git tag v2.2.46`
   - `git push origin v2.2.46`
3) GitHub Actions -> workflow `Flutter Tag Build` runs and uploads APK artifact.

### A3) Verification on device
1) Install APK from CI artifact.
2) Run tests:
   - Buy Basic + Enterprise on same device.
   - Verify paid history shows both licenses.
   - Logout and re-open License page:
     - Active license card cleared.
     - Paid history still visible.
   - Try to generate trial twice:
     - Second attempt must be blocked.
3) Collect proof:
   - APK version, screenshots, `/user/history` response.
4) Update `opus_verification_phase4b.md` and send to Codex.

Acceptance: Phase 4b is approved after all above tests pass.

## Workstream B - Phase 4 (Admin Dashboard Rebuild)
Reference: `docs/team-notes/codex_phase4_dashboard_rebuild_plan_20260101.md`

### B1) Decide hosting
- Option A: serve `/admin` from FastAPI.
- Option B: Nginx serves static `admin/` folder.

### B2) Implement UI scaffold
- Create `admin/index.html`, `admin/assets/css/app.css`, `admin/assets/js/*`.
- Build layout: sidebar + top bar + content grid.

### B3) Implement pages
- Overview, Licenses, Orders, Products, Tiers, Devices, Trials, Connections, Notifications, Analytics, System Health, Settings.
- Use JWT-only admin auth.

### B4) QA
- Manual tests for each tab.
- Verify search, filters, bulk actions.

Acceptance: new dashboard fully replaces old admin UI.

## Workstream C - Phase 5 (Cleanup + Refactor)
1) Remove dead scripts and duplicate docs.
2) Normalize API docs (`docs/openapi.yaml`, `docs/api_contract.md`).
3) Refactor `server_app.py` into modules (routes/services/models).
4) Align error response format everywhere.
5) Add lint rules (format + basic static checks).

Acceptance: smaller server entrypoint, consistent docs, reduced maintenance cost.

## Workstream D - Phase 6 (Automation / CI)
1) Add smoke tests to CI (critical endpoints).
2) Add webhook test runner (signed + invalid payloads).
3) Add release pipeline:
   - Build APK, upload artifact, optional signing.
4) Add basic secrets scanning (pre-commit or CI).

Acceptance: CI verifies API + client contract on each release.

## Workstream E - Phase 7 (Performance + Security)
1) Load tests for:
   - `/payment/bank/webhook`, `/user/history`, `/license/info`
2) DB indexes:
   - `licenses.created_at`, `bank_orders.trans_code`, `license_devices.license_key`
3) Security audit:
   - JWT expiry rules, webhook signature checks, rate limits.
4) Dependency scanning (server + Flutter).

Acceptance: stable under load, documented security posture.

## Sign-off
Codex Team - 2026-01-01
