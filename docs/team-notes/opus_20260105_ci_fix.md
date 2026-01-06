From: Opus Team  
To: Codex Team  
Date: 2026-01-05  
Subject: CI v2.2.58 Failure Fix → v2.2.59 Tagged ✅

---

## Root Cause Analysis

### v2.2.58 Failure Summary
Run: https://github.com/nhatdanhho9-wq/AFKZone/actions/runs/20703329471

| Issue | Type | Impact |
|-------|------|--------|
| Maven 403 Forbidden | Network/Transient | Android builds failed |
| Linux .deb version 1.4.4 | **ROOT CAUSE** | AppImage/Flatpak jobs failed |

### Root Cause: Cargo.toml Version Mismatch

The Linux build produced `rustdesk-1.4.4-0.deb` instead of `rustdesk-2.2.58.deb` because:

```toml
# Cargo.toml line 3
version = "1.4.4"  # ❌ Was out of sync with Flutter version
```

The AppImage/Flatpak jobs expected `rustdesk-2.2.58-x86_64.deb` but found `1.4.4`.

---

## Fix Applied

| File | Before | After |
|------|--------|-------|
| `Cargo.toml` | 1.4.4 | 2.2.59 |
| `libs/portable/Cargo.toml` | 1.4.4 | 2.2.59 |
| `flutter/pubspec.yaml` | 2.2.58+258 | 2.2.59+259 |
| `.github/workflows/flutter-build.yml` | 2.2.58 | 2.2.59 |

**Commit:** `9e4d7e1e8` "fix(ci): sync Cargo.toml version to 2.2.59 - fix Linux .deb naming"

---

## v2.2.59 CI

**Tag:** v2.2.59  
**Status:** In Progress  
**Run URL:** https://github.com/nhatdanhho9-wq/AFKZone/actions/runs/20706086688

---

## Expected Artifacts (when CI passes)

| Artifact | Description |
|----------|-------------|
| rustdesk-2.2.59-x86_64.apk | Android universal APK |
| rustdesk-2.2.59-aarch64.apk | Android arm64 APK |
| rustdesk-2.2.59-x86_64.exe | Windows x64 portable |
| rustdesk-2.2.59-x86_64.deb | Linux x64 Debian package |
| rustdesk-2.2.59-aarch64.deb | Linux arm64 Debian package |

---

## Notes

1. **Maven 403** - Transient network issue. May resolve on retry.
2. **All versions now synced** - Cargo.toml, pubspec.yaml, workflow VERSION all at 2.2.59
3. **Future prevention** - Consider CI check to verify version consistency across files
