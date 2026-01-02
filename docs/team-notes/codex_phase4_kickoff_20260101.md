# Phase 4 Kickoff - Admin Dashboard Rebuild

Date: 2026-01-01
Owner: Codex Team
Audience: Opus Team (implementation)

## Status
- Phase 4 started
- Old admin dashboard should be removed or archived after new dashboard is accepted.

## Immediate Actions (Opus)
1) Confirm hosting approach for new dashboard:
   - Option A: API serves `/admin` (HTML + assets).
   - Option B: Static host (nginx) at `/admin/`.
2) Create new dashboard folder structure (per Phase 4 plan).
3) Implement login flow (JWT only) and global API wrapper.
4) Build core tabs: Overview, Licenses, Orders, Products, Tiers.
5) Build secondary tabs: Devices, Trials, Connections, Notifications, Analytics.
6) QA: verify each tab loads data + actions work.
7) Remove or archive old dashboard files after acceptance.

## Deliverables
- New admin UI (HTML/CSS/JS)
- JWT-only auth flow
- Full admin coverage for current endpoints
- Mobile responsive layout

## Exit Criteria
- All tabs load with real data
- All actions execute without errors
- Clear error handling (401 -> logout)
- Stakeholder acceptance

## Reference
- See `docs/team-notes/codex_phase4_dashboard_rebuild_plan_20260101.md`

## Sign-off
Codex Team
