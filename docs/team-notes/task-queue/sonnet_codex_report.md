# Sonnet → Codex Report

## Status: IN_PROGRESS
## Timestamp: 2026-01-10T22:55:00+07:00
## Task: P0 – WebSocket "not upgraded" on host

---

## ACK
- 30s watcher: Confirmed active
- First ACK: 2026-01-10T22:34:00+07:00
- Update: 2026-01-10T22:55:00+07:00

## Root Cause Found
Host was connecting WS **before** getting host_token from host-ready:
```
_initSession() → connectSignaling(wsToken: null) → empty token → http error
```

## Fix Applied (commit pending)

### BEFORE (broken):
```
1. approve → navigate to RemoteSessionScreen
2. _initSession → connectSignaling(wsToken: null) ← FAILS (http not ws)
3. Wait for enable_screen_capture WS ← never received
```

### AFTER (fixed):
```
1. approve → navigate to RemoteSessionScreen(requestId=...)
2. _initSession → DO NOT connect WS
3. Show MediaProjection dialog immediately
4. User clicks OK → MediaProjection starts
5. POST /remote/host-ready → get host_token
6. connectSignaling(wsToken: host_token) ← NOW WORKS
```

## Changes Made
| File | Change |
|------|--------|
| remote_session.dart | Host skips WS connect in _initSession |
| remote_session.dart | Show MediaProjection dialog immediately |
| remote_session.dart | Connect WS AFTER host-ready returns token |

## Next Steps
- Build APK with fix
- User tests and shares logcat

## Status: IN_PROGRESS
