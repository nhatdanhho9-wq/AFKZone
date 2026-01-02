# Codex Review - Opus Status Report 20260102

Date: 2026-01-02
Owner: Codex Team
Audience: Opus Team + Sonnet Team

## Decision (confirmed)
- Work distribution = **Option B (Parallel)**.
- Phase 4 Dashboard Owner = **Sonnet**.

## Adjusted Work Split (final)
- Opus: Server/API/DB fixes, CI/tag builds, deployments.
- Sonnet: Flutter client + Admin dashboard UI.
- Codex: QA gate + runtime verification + final approval.

## Required Actions (immediate)
1) Phase 4b CI build:
   - Confirm tag build `v2.2.46` produces APK artifact.
   - Share APK link + version with Codex.
2) Phase 4b verification (Opus):
   - Install APK, run logout/history/trial tests.
   - Share screenshots + `/user/history` response.
3) Phase 4b server fixes (Opus):
   - Disable webhook bypass (`DEV_BYPASS_SIGNATURE` must be off).
   - Ensure `/user/history` returns `is_trial` and filters by it.
4) Phase 4 dashboard start (Sonnet):
   - Create `admin/` scaffold per plan.
   - Post first UI draft screenshots + file list.

## Notes
- Naming: use **Sonnet** consistently (not “Sonet”).
- CI: APK artifact is only uploaded via `Flutter Tag Build` workflow.

## Pending for Codex Approval
Codex will approve Phase 4b only after:
- APK verification evidence,
- Server fixes confirmed (no webhook bypass),
- `/user/history` includes `is_trial`.

## Sign-off
Codex Team - 2026-01-02
