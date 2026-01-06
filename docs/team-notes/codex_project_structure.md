AFKZone Project Structure and Team Operating Guide
Date: 2026-01-03
Owner: Codex Team

Purpose
- Single source of truth for project structure, team roles, policies, and reporting.
- Designed for Antigravity single-app workflow (shared app, single opened workspace).

Project Overview
- Product: AFKZone (remote desktop + licensing + payments).
- Core services:
  - API: https://api.afkzone.cloud
  - Admin UI: https://admin.afkzone.cloud
  - ID/Rendezvous: https://id.afkzone.cloud
- Payments: Casso webhook V2 -> /payment/bank/webhook (legacy), /webhook/casso (canonical).

Repository Structure (D:\rustdesk-dev)
- admin/                  # Admin dashboard (static site)
- flutter/                # Mobile + desktop Flutter UI
- src/, libs/             # RustDesk core codebase
- server_app.py           # License/payment API server
- docs/                   # Project docs and team reports
  - docs/team-notes/      # All team reports and Codex guidance

Team Structure (Current)
- Codex Team (PM/QA/Coordinator)
  - Assigns tasks, verifies critical fixes, approves go-ahead.
- Opus Team (Core)
  - Server/API/DB, deployments, production ops, CI build and release.
- OpusB Team (Security/CI)
  - Security hardening, CI stability, infrastructure fixes (no UI work).
- OpusC Team (QA/Integration)
  - Runtime verification, smoke tests, release checks, log review.
- Sonnet Team (UI)
  - Mobile Flutter UI + Admin dashboard UI (admin/** and flutter/** only).
  - Note: Sonnet Team name is kept for report continuity even if staffing changes.

Scope Boundaries (Strict)
- Opus/OpusB/OpusC: server_app.py, DB, CI, deploy, infra.
- Sonnet Team: flutter/**, admin/**.
- Cross-team edits require Codex approval.

Antigravity Single-App Workflow
- Only Opus opens the workspace folder in Antigravity.
- Other teams must NOT click "Open Folder" (avoids taking over workspace).
- Use absolute paths (D:\rustdesk-dev\...) for reads/writes.
- Reports always saved under docs/team-notes/.

Task Assignment Policy
- Parallel tasks: send email only to teams that must act immediately.
- Sequential tasks: send one email to the active team, wait for completion, then
  send the next task to the next team.
- Each task must be labeled RUNNING or WAITING_ON_X.

Reporting Rules (Mandatory)
- All reports go to docs/team-notes/.
- File naming:
  - Opus:    opus_YYYYMMDD_*.md
  - OpusB:   opusb_YYYYMMDD_*.md
  - OpusC:   opusc_YYYYMMDD_*.md
  - Sonnet:  sonnet_YYYYMMDD_*.md
- Each report must include:
  - Status (COMPLETE / IN_PROGRESS / BLOCKED)
  - Summary (2-5 bullets)
  - Changes (files, commits, deployments)
  - Tests/verification
  - Risks/notes
  - Next steps / asks

Email Template (Required Format)
From: <Team Name>
To: Codex Team
Subject: <Short summary>
Status: <COMPLETE / IN_PROGRESS / BLOCKED>

Body:
- What changed
- Evidence (commit hash, logs, URL)
- Tests performed
- Request/decision needed

QA/Verification Policy
- Teams perform full tests for their scope.
- Codex verifies a small set of critical checkpoints (evidence-driven).
- If a report is missing evidence, it is not accepted.

Release Flow (High Level)
1) Sonnet/Opus commits fixes
2) Opus tags release + triggers CI
3) Artifacts produced (APK, desktop builds)
4) QA validation (OpusC/Opus or user)
5) Codex approves or requests fixes

Security Rules
- No secrets in code. All secrets in .env.
- Webhook signatures must be verified (no permanent bypass).
- Admin credentials must be rotated after fixes.

Current Known Issues (Track in reports)
- Any CI failure must include full error excerpt and root cause.
- Any admin UI JS console error blocks login and must be fixed first.

Contact and Escalation
- Only Codex Team assigns tasks.
- Escalate blockers in report with explicit ask.
