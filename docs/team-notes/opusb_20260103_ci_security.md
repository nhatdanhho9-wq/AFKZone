From: OpusB Team
To: Codex Team
Date: 2026-01-03
Subject: CI Fixes Ready - NASM Retry Logic + CORS Tighten

Status: COMPLETE

## Summary

- Changed NASM install approach: removed mirror requirement, added retry logic (3 attempts)
- Added artifact existence precheck for AppImage/Flatpak builds
- Tightened CORS for admin UI
- All code changes ready for push
- Report: docs/team-notes/opusb_20260103_ci_security.md

## Changes

- .github/workflows/flutter-build.yml#L634-675: NASM retry logic (3 attempts, 10s delay)
- .github/workflows/flutter-build.yml#L1880-1900: AppImage artifact precheck
- .github/workflows/flutter-build.yml#L1964-1984: Flatpak artifact precheck
- server_app.py#L81-97: CORS restricted to admin.afkzone.cloud, api.afkzone.cloud

## Tests

- YAML syntax: PASS
- Python syntax: PASS
- nasm.us connectivity: FAIL (unreachable from both OpusB and Codex)
- CI run: Pending push

## Risks / Blockers

- nasm.us currently unreachable - CI may fail on macOS builds if nasm.us remains down
- Retry logic will help with intermittent failures
- No SHA256 verification (cannot download file to get checksum)

## Next Steps

- Push workflow fixes + CORS changes to trigger CI
- Monitor macOS build step for NASM download success/failure
- If nasm.us remains down, consider alternative: brew install nasm@2 or cache in GitHub Actions

## Evidence

- Report: docs/team-notes/opusb_20260103_ci_security.md (created)
- nasm.us error: curl: (28) Failed to connect to www.nasm.us port 443 after 21182 ms
