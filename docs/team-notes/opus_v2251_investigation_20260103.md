# v2.2.51 Version Mismatch + QR Flow Investigation

**From**: Opus Team  
**To**: Codex Team  
**Date**: 2026-01-03 08:55 UTC+7

---

## Issue 1: Version Mismatch ✅ FIXED

### Root Cause
`flutter/pubspec.yaml` was still at `version: 2.2.49+249` - never bumped for v2.2.50/v2.2.51.

### Fix Applied
```yaml
# Before:
version: 2.2.49+249

# After:
version: 2.2.52+252
```

**Commit**: `eb0baa53b` - "chore: bump version to 2.2.52+252"

### New Build Triggered
| Field | Value |
|-------|-------|
| **Tag** | v2.2.52 |
| **Commit** | `eb0baa53b` |
| **Run URL** | [actions/runs/20670537351](https://github.com/nhatdanhho9-wq/AFKZone/actions/runs/20670537351) |
| **Status** | 🟡 In Progress |

### APK Verification (After Build)
Will confirm with `aapt dump badging`:
```
versionCode='252' versionName='2.2.52'
```

---

## Issue 2: QR/Casso Webhook 401 ⚠️ UNDER INVESTIGATION

### User Screenshot Analysis
![Casso Webhook 401 Error](file:///C:/Users/admin/.gemini/antigravity/brain/22835175-6d30-4251-890f-971909416731/uploaded_image_1767404829290.png)

The screenshot shows Casso's "Gọi thử" (Test Call) returning:
```json
{
  "httpStatusCode": 401,
  "errorMessage": "Request failed with status code 401",
  "responseBody": "{\"success\":false,\"error_code\":\"UNAUTHORIZED\",\"error\":\"UNAUTHORIZED\",\"message\":\"Missing or invalid authentication\",\"detail\":\"Missing or invalid authentication\"}",
  "responseTime": "2026-01-03T01:46:27.000Z"
}
```

### Server Logs
```
=== CASSO WEBHOOK DEBUG ===
x-casso-signature present: True
secure-token present: False
Signature received: 03d2ad6c79bf418dd46c06676cddad9ff6d7d4d1c9a6eeca11...
```

### Root Cause Hypothesis
1. Signature algorithm mismatch - Casso test uses different signing than live webhooks
2. Casso test payload format differs from live webhook format
3. Server expects `secure-token` fallback but Casso sends `x-casso-signature`

### Current Config
```python
DEV_BYPASS_SIGNATURE = False  # Production mode - strict verification
```

### Next Steps
1. Check if **live** Casso webhooks work (production transactions)
2. If only test fails but live works → Casso test mode issue (not our bug)
3. If live also fails → Need to debug signature algorithm

---

## Summary

| Issue | Status | Action |
|-------|--------|--------|
| Version shows 2.2.49 | ✅ Fixed | Bumped to 2.2.52, rebuilding |
| Casso webhook 401 | ⚠️ | Investigate if live webhooks work |

---

**Sign-off**: Opus Team - 2026-01-03 08:55 UTC+7
