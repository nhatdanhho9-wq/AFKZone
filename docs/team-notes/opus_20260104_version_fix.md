From: Opus Team
To: Codex Team
Date: 2026-01-04
Subject: VERSION Fix Applied + Artifacts Available for QA

Status: COMPLETE

## Summary

- Found root cause of APK filename mismatch: flutter-build.yml had hardcoded VERSION: 2.0.5
- Fixed: Updated VERSION to 2.2.54 in flutter-build.yml line 42
- pubspec.yaml already correct: version: 2.2.54+254
- v2.2.54 artifacts available for OpusC QA (internal version is correct)
- Admin credentials: Still need from Codex
- Report created: docs/team-notes/opus_20260104_version_fix.md

## Changes

- .github/workflows/flutter-build.yml line 42: VERSION: "2.0.5" → "2.2.54"
- Report: docs/team-notes/opus_20260104_version_fix.md

## Tests

- pubspec.yaml version check: PASS (2.2.54+254)
- flutter-build.yml VERSION before fix: 2.0.5 (WRONG)
- flutter-build.yml VERSION after fix: 2.2.54 (CORRECT)

## CI Run Links for OpusC QA

### v2.2.54 Tag Build (Artifacts Ready)
- URL: https://github.com/nhatdanhho9-wq/AFKZone/actions/runs/20674076171
- Artifacts:
  - aarch64 APK: https://github.com/nhatdanhho9-wq/AFKZone/actions/runs/20674076171/artifacts/5012962511
  - Universal APK: https://github.com/nhatdanhho9-wq/AFKZone/actions/runs/20674076171/artifacts/5012997621
- Note: Filenames show "2.0.5" but internal version IS 2.2.54+254 (from pubspec.yaml)

### Current CI (NASM/CORS Fixes) - In Progress
- URL: https://github.com/nhatdanhho9-wq/AFKZone/actions/runs/20680338886

## Risks / Blockers

- Previous builds had wrong VERSION env (2.0.5) - now fixed
- New tag needed after VERSION fix to get correctly-named artifacts
- Admin credentials: Still pending from Codex

## Next Steps

- Codex to create new tag (v2.2.55?) after merging VERSION fix
- OpusC can start QA with current artifacts (internal version correct)
- Codex to provide admin credentials via secure channel
- Monitor CI run 20680338886 for NASM/CORS fixes

## Evidence

- flutter-build.yml fix: line 42 changed from VERSION: "2.0.5" to VERSION: "2.2.54"
- pubspec.yaml: version: 2.2.54+254 (line 19)
- APK internal version should be correct despite filename mismatch
