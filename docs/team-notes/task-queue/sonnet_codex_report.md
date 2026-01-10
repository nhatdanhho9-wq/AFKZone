# Sonnet → Codex Report

## Status: ACK
## Timestamp: 2026-01-10T22:34:00+07:00
## Task: P0 – WebSocket "not upgraded" on host

---

## Actions Taken

### 1. Added WS URL Logging (webrtc_service.dart)
- Log token presence before building URL
- Log URL scheme (ws/wss)
- Log URL host:port
- Log URL path
- Log masked URL with token prefix
- Verify scheme is ws:// or wss:// before connecting
- Show clear error if scheme is invalid

### 2. Logging Format
```
[WebRTC] connectSignaling: token=present (64 chars) / EMPTY/NULL
[WebRTC] WS URL scheme: ws
[WebRTC] WS URL host: 171.253.168.44:21121
[WebRTC] WS URL path: /sessions/{sessionId}/ws
[WebRTC] WS URL (masked): ws://171.253.168.44:21121/sessions/{sessionId}/ws?token=abc1234567...
[WebRTC] Attempting WebSocket connect...
[WebRTC] WebSocket connected successfully / WS error: ...
```

### 3. Schema Conversion Check
- `signalingUrl` at line 366 correctly converts:
  - `http://` → `ws://`
  - `https://` → `wss://`

### 4. Potential Issues Identified
- If `wsToken` is empty string, WS upgrade will likely fail
- Host pre-token mode passes null → becomes empty string → server may reject

## Next Steps
- Building APK with logging
- User to test and share logcat output
- If token empty, investigate why host-ready didn't return token

## Status: IN_PROGRESS
