# Codex Instructions for Sonnet - Phase 4 Dashboard

Date: 2026-01-02
Owner: Codex Team
Audience: Sonnet Team

## Start Mode
- **Parallel** with Opus. No dependency on Phase 4b verification.
- Scope is isolated to `admin/` UI only.

## Primary Plan File (read first)
- `docs/team-notes/codex_phase4_dashboard_rebuild_plan_20260101.md`

## Scaffold Requirements (must follow)
Create this structure:
```
admin/
  index.html
  assets/
    css/app.css
    js/app.js
    js/api.js
    js/ui.js
    js/pages/
      overview.js
      licenses.js
      orders.js
      products.js
      tiers.js
      devices.js
      trials.js
      connections.js
      notifications.js
      analytics.js
      health.js
      settings.js
```

## Implementation Order (step-by-step)
1) **Layout + Tokens**
   - Implement sidebar, top bar, content area.
   - Add CSS variables + fonts per plan.
2) **Auth + API client**
   - Login form -> `/admin/login` -> store JWT.
   - `apiFetch()` injects `Authorization: Bearer <token>`, handles 401.
3) **Overview page**
   - KPI cards + basic charts placeholder.
4) **Licenses page**
   - Table, search, revoke/unrevoke, extend.
5) **Orders page**
   - List + manual complete.
6) Remaining pages in this order:
   - Products, Tiers, Devices, Trials, Connections, Notifications, Analytics, System Health, Settings.

## Output Required (for Codex review)
- New files list.
- Screenshots: login, overview, licenses table.
- Short note: what’s mocked vs real API.
- Report file: `sonnet_update_YYYYMMDD.md` in `docs/team-notes/`.

## Notes
- Do not modify server endpoints without Codex request.
- Use only admin JWT auth (no admin_key).

## Sign-off
Codex Team - 2026-01-02
