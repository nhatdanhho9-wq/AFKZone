# Collaboration Structure - Codex + Opus + Sonnet

Date: 2026-01-01
Owner: Codex Team
Audience: Opus Team + Sonnet Team

## Goal
Reduce conflicts, increase speed, and keep one source of truth.

## Roles (clear ownership)
- Codex: Project manager + QA gate + runtime verification + final review.
- Opus: Server/API/DB + CI builds + deployments.
- Sonnet: Client (Flutter) + Admin Dashboard UI + UI/UX fixes.

## Work Lanes (no overlap)
Lane A (Server/API): `server_app.py`, DB migrations, `docs/openapi.yaml` -> Opus
Lane B (Flutter Client): `flutter/lib/**` -> Sonnet
Lane C (Admin UI): `admin/**` (new dashboard) -> Sonnet
Lane D (Review/Docs): `docs/team-notes/**` -> Codex

## Source of Truth
- API contract: `docs/openapi.yaml`
- Phase plans: `docs/team-notes/codex_next_steps_plan_20260101.md`
- Audit tasks: `docs/team-notes/codex_audit_tasks_20260101.md`
- Runtime report: `docs/team-notes/codex_runtime_review_20260101.md`

## Workflow (every task)
1) Codex posts task file in `docs/team-notes/`.
2) Opus/Sonnet implement in their lane only.
3) Opus/Sonnet post report in `docs/team-notes/` with:
   - Files touched
   - Commands run
   - Test results
4) Codex runs runtime checks + posts review file.
5) Only after Codex approval, move to next task.

## File Naming (keep consistent)
- Codex review: `codex_review_YYYYMMDD_<topic>.md`
- Team updates: `opus_update_YYYYMMDD.md`, `sonnet_update_YYYYMMDD.md`
- Handoff: `opus_handoff_YYYYMMDD.md`, `sonnet_handoff_YYYYMMDD.md`

## Current Sprint Tasks (Phase 4b + Audit)

### Opus (Server + CI)
1) Disable webhook bypass:
   - Remove `DEV_BYPASS_SIGNATURE` or set to False.
2) /user/history:
   - Return `is_trial` and filter by it (not by tier).
3) Enforce JWT-only:
   - Convert `/generate` and `/list` to JWT (remove admin_key).
4) CI APK build (tag flow):
   - Bump version in `flutter/pubspec.yaml`
   - Tag `v2.2.46`, push tag, run `Flutter Tag Build`
5) Post report with APK version + artifact link.

### Sonnet (Flutter + Admin UI)
1) Stabilize device fingerprint:
   - Use Android `androidId` or persistent UUID (no Build.ID).
2) License history UI:
   - Use `is_trial` from server response.
3) Remove duplicate `_checkDirtyFlag()` call.
4) Start Phase 4 admin dashboard scaffold:
   - Create `admin/` structure and layout per plan.
5) Post report with screenshots (UI pages) and files changed.

### Codex (QA/Review)
1) Runtime re-check after server fix.
2) Review Sonnet UI changes (code review + runtime notes).
3) Update review file and approve Phase 4b when tests pass.

## Definition of Done
- Code merged in correct lane.
- CI build artifact produced (for client changes).
- Runtime verification passed.
- Codex review posted and approved.

## Sign-off
Codex Team - 2026-01-01
