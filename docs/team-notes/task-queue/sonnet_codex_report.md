# Sonnet → Codex Report

## Status: DONE (Client-Side)
## Timestamp: 2026-01-11T00:05:00+07:00
## Task: P0 – Host-ready 500 non-JSON

---

## ACK
- 30s watcher: RUNNING
- First ACK: 2026-01-10T22:34:00+07:00
- Update: 2026-01-11T00:05:00+07:00

## Sonnet Tasks COMPLETED

| Task | Status | Commit |
|------|--------|--------|
| Log host-ready raw response | ✅ DONE | 8199f7d0f |
| Dedup MediaProjection dialog | ✅ DONE | 8199f7d0f |
| Share session info | ✅ See below |

### Raw Response Logging (Working)
User confirmed seeing:
```
Host ready failed: Server returned non-JSON response (500)
```
This proves our logging is working and catching the 500 error.

### Session Info
Device: `doo6EtReB-d7EaqtiY0ttKmD`

Query commands for Opus team:
```bash
curl "http://171.253.168.44:21121/remote/last-session?device_id=doo6EtReB-d7EaqtiY0ttKmD"
curl "http://171.253.168.44:21121/sessions/<session_id>/status?include_lifecycle=true"
```

## Root Cause (BACKEND)
**The 500 error is from `/remote/host-ready` endpoint returning non-JSON (HTML error page).**

Opus team must investigate:
1. Why `/remote/host-ready/{request_id}` returns 500
2. Check backend logs for exception
3. Verify route is registered correctly
4. Fix and return proper JSON response

## APK (Latest)
SHA256: `3BF81D1B44A9B9BB189A569645F84FA279CEF9B162EB19094251E88C7273D0BB`

## Status: BLOCKED (Waiting for Opus backend fix)
