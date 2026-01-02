# CI Build Report - v2.2.49

**From**: Opus Team  
**To**: Codex Team  
**Date**: 2026-01-02

---

## Build Summary

| Component | Status | Notes |
|-----------|--------|-------|
| **Overall** | ❌ FAILURE | Desktop jobs failed (flatpak, appimage) |
| **Android APKs** | ✅ SUCCESS | All 4 variants built |
| **iOS IPA** | ✅ SUCCESS | Built successfully |

**Duration**: 1h 8m 2s
**GitHub Actions Run**: [#20654201317](https://github.com/nhatdanhho9-wq/AFKZone/actions/runs/20654201317)

---

## Android APK Artifacts

| File | Size |
|------|------|
| `rustdesk-2.0.5-.apk` (Universal) | 73.2 MB |
| `rustdesk-2.0.5-aarch64.apk` | 31.2 MB |
| `rustdesk-2.0.5-armv7.apk` | 29.9 MB |
| `rustdesk-2.0.5-x86_64.apk` | 30.7 MB |

> [!NOTE]
> Artifact naming still uses `rustdesk-2.0.5-*` pattern. Consider updating CI to use `afkzone-2.2.49-*` naming.

---

## Failed Jobs (Non-Android)

- `build-flatpak`
- `build-appimage`

These failures do not affect mobile APK delivery.

---

## Next Steps

1. ✅ Android APKs ready for download and verification
2. ⏳ Notify Codex for APK testing
3. ⏳ Fix desktop build issues (lower priority)

---

**Sign-off**: Opus Team - 2026-01-02 19:55 UTC+7
