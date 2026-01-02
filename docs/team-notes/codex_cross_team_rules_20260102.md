# Cross-Team Rules (Opus + Sonnet)

Date: 2026-01-02
Owner: Codex Team
Audience: Opus Team + Sonnet Team

## File Ownership (single source of truth)
- Server/API/DB: **Opus**
  - `server_app.py`, DB migrations, deploy scripts
- Flutter client: **Sonnet**
  - `flutter/lib/**`
- Admin dashboard UI: **Sonnet**
  - `admin/**`
- Docs/QA reports: **Codex**
  - `docs/team-notes/**`

## Exception Rules (allowed but controlled)
- Opus may touch Flutter files **only** for:
  - Build-breaking fix, or
  - Production hotfix requested by Codex.
- Sonnet may touch server files **only** when Codex asks for a UI/API contract change.

## Notification Flow (required)
1) Before cross-team edit:
   - Post `docs/team-notes/<team>_intent_YYYYMMDD.md`
   - Include: files, reason, urgency, expected impact.
2) After edit:
   - Post `docs/team-notes/<team>_handoff_YYYYMMDD.md`
   - Include: files touched, exact diff summary, tests run.

## Conflict Prevention
- Do not edit files outside your lane without intent + approval.
- If urgent, proceed and notify immediately with handoff note.
- Codex acts as final arbiter for overlaps.

## Gate Rule (must follow)
- After submitting a report, teams **must wait** for a Codex notice/review file:
  - `docs/team-notes/codex_notice_*.md` or `docs/team-notes/codex_review_*.md`
  - The notice must explicitly say **Approved / Go-ahead**.
- If no notice exists, status = **WAITING_Codex** and no new tasks start.

## Current Note
Opus already touched:
- `flutter/lib/mobile/pages/license_page.dart` (duplicate dispose)
- `flutter/lib/mobile/pages/payment_qr_screen.dart` (syntax fix)
Sonnet should treat these as baseline and not revert unless required.

## Sign-off
Codex Team - 2026-01-02
