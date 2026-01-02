# Codex Notice - Phase 2 Scope Decision (Sonnet)

Date: 2026-01-02
From: Codex Team
To: Sonnet Team

## Decision: Option C (Hybrid)
We will use a hybrid scope to keep velocity without sacrificing critical CRUD.

### Full CRUD Required
- Products (`/admin/products`)
- Tiers (`/admin/tiers`)
- Notifications (`/admin/notifications`)
- Trials (`/admin/trial-devices`) includes: list, delete, clear-all

### Read-Only (Basic View) for now
- Devices (`/admin/devices/detailed`)
- Connections (`/admin/connections`)
- Analytics (`/admin/analytics/revenue`) - chart placeholder ok
- System Health (`/health`) - status panel ok
- Settings (info display only)

## Implementation Order
1) Products (CRUD)
2) Tiers (CRUD)
3) Trials (list + delete + clear-all)
4) Notifications (CRUD)
5) Devices (list)
6) Connections (list)
7) Analytics (charts placeholder)
8) System Health (status panel)
9) Settings (info display)

## Reporting
Use `sonnet_update_YYYYMMDD.md` with:
- Files touched
- Tests run
- Screenshots (Products + Tiers + Trials at minimum)

## Sign-off
Codex Team - 2026-01-02
