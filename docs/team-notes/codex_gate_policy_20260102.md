# Codex Gate Policy (Work Must Wait for Notice)

Date: 2026-01-02
Owner: Codex Team
Audience: Opus Team + Sonnet Team

## Purpose
Prevent teams from moving forward without explicit approval.

## Rule
After any report is submitted, teams must wait for a Codex notice/review:
- `docs/team-notes/codex_notice_*.md`
- `docs/team-notes/codex_review_*.md`
Only continue if the notice contains **Approved / Go-ahead**.

## Status Tags (use in reports)
- `Status: WAITING_Codex`
- `Status: APPROVED`
- `Status: BLOCKED`

## Standard Flow
1) Team posts report → Status: WAITING_Codex
2) Codex posts notice/review → Status: APPROVED or BLOCKED
3) Team proceeds only after APPROVED

## Report Template (teams should use)
```
Status: WAITING_Codex
Files touched:
Tests run:
Next step (requested):
```

## Sign-off
Codex Team - 2026-01-02
