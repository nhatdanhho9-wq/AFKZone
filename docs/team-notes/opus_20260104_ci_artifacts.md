From: Opus Team
To: Codex Team
Date: 2026-01-04
Subject: CI Run Links + Artifacts Available - Ready for QA

Status: COMPLETE

## Summary

- Found CI runs for v2.2.54 with artifacts available
- v2.2.54 tag build: FAILED but 12 artifacts produced (APKs ready)
- Current CI run with NASM/CORS fixes: IN PROGRESS
- Admin credentials: Need Codex to provide (not in codebase)
- Report created: docs/team-notes/opus_20260104_ci_artifacts.md

## Changes

- No code changes (information gathering only)
- Report: docs/team-notes/opus_20260104_ci_artifacts.md

## Tests

- GitHub Actions access: PASS (repo: nhatdanhho9-wq/AFKZone)
- v2.2.54 artifacts check: PASS (12 artifacts available)

## CI Run Links

### v2.2.54 Tag Build (Artifacts Available)
- URL: https://github.com/nhatdanhho9-wq/AFKZone/actions/runs/20674076171
- Status: FAILED (some jobs failed)
- Commit: 742203d - "chore: bump version to 2.2.54+254"
- Artifacts (12 total):
  - rustdesk-2.0.5-aarch64.apk (31.2 MB)
  - rustdesk-2.0.5-armv7.apk (29.9 MB)
  - rustdesk-2.0.5-x86_64.apk (30.7 MB)
  - rustdesk-2.0.5-.apk - Universal (73.2 MB)
  - rustdesk-unsigned-windows-x86/x86_64
  - Various library files (.a, .so)

### Current NASM/CORS Fixes Build (In Progress)
- URL: https://github.com/nhatdanhho9-wq/AFKZone/actions/runs/20680338886
- Status: IN PROGRESS (~15 min running)
- Commit: b43f09f - "fix(ci): NASM retry logic + artifact precheck + CORS tighten"
- Artifacts: None yet (building)

## Risks / Blockers

- v2.2.54 build partially failed (macOS jobs)
- APK filenames show "2.0.5" instead of "2.2.54" (version mismatch in config?)
- Admin credentials: Still need from Codex

## Next Steps

- OpusC can download APK artifacts from run 20674076171 for QA
- Need Codex to provide admin credentials via secure channel
- Monitor current CI run (20680338886) for NASM/CORS fixes completion
- Investigate version mismatch in APK filenames

## Evidence

- CI Run v2.2.54: https://github.com/nhatdanhho9-wq/AFKZone/actions/runs/20674076171
- CI Run NASM Fix: https://github.com/nhatdanhho9-wq/AFKZone/actions/runs/20680338886
- Repo: nhatdanhho9-wq/AFKZone
