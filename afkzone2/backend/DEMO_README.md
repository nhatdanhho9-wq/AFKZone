# OpusD Signaling Demo

## Quick Start

### 1. Setup (one time)
```powershell
cd D:\rustdesk-dev\afkzone2\backend

# Create Python 3.12 venv (required due to pydantic-core issue with 3.14)
py -3.12 -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install httpx websockets
```

### 2. Set Environment Variables
```powershell
$env:AFK_ADMIN_USER = "admin"
$env:AFK_ADMIN_PASS = "demo-password"
$env:AFK_SIGNING_SEED_B64 = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
```

### 3. Start Server
```powershell
uvicorn app.main:app --reload --port 8081
```

### 4. Run Demo (2 terminals)

**Terminal 1 - Controller:**
```powershell
cd D:\rustdesk-dev\afkzone2\backend
.\.venv\Scripts\activate
python demo_controller.py host-device-001
```

**Terminal 2 - Host:**
```powershell
cd D:\rustdesk-dev\afkzone2\backend
.\.venv\Scripts\activate
python demo_host.py host-device-001
```

### 5. Expected Output

**Controller:**
```
[HH:MM:SS] CONTROLLER: Starting session for target device: host-device-001
[HH:MM:SS] CONTROLLER: POST /sessions/start
[HH:MM:SS] CONTROLLER: Session created: abc123...
[HH:MM:SS] CONTROLLER: Sending SDP offer...
[HH:MM:SS] CONTROLLER: Received: sdp_answer from host
[HH:MM:SS] CONTROLLER: 🎉 control_ready received! Session fully established!
```

**Host:**
```
[HH:MM:SS] HOST: Attached to session: abc123...
[HH:MM:SS] HOST: Received: sdp_offer from controller
[HH:MM:SS] HOST: Sending SDP answer...
[HH:MM:SS] HOST: 🎉 control_ready sent! Session fully established!
```

### 6. Rate Limit Test
```powershell
python demo_rate_limit.py
```

### 7. Check Audit Log
```powershell
curl http://localhost:8081/sessions/audit
```

## Demo Flow

```
Controller                    Signaling Server                    Host
    |                              |                               |
    |-- POST /sessions/start ----->|                               |
    |<-- session_id, token --------|                               |
    |                              |                               |
    |                              |<-- POST /sessions/host/attach --|
    |                              |-- session_id, token ----------->|
    |                              |                               |
    |-- WS connect --------------->|<-- WS connect -----------------|
    |                              |                               |
    |-- sdp_offer ---------------->|-- forward ------------------>|
    |                              |                               |
    |<-- sdp_answer --------------- |<-- sdp_answer ----------------|
    |                              |                               |
    |-- ice_candidate ------------>|-- forward ------------------>|
    |<-- ice_candidate ----------- |<-- ice_candidate -------------|
    |                              |                               |
    |<-- control_ready ----------- |<-- control_ready -------------|
    |                              |                               |
    v                              v                               v
         WebRTC P2P connection established (not shown)
```

## Files

| File | Description |
|------|-------------|
| `app/signaling.py` | Signaling service implementation |
| `app/main.py` | FastAPI app (mounts signaling router) |
| `demo_controller.py` | Controller demo script |
| `demo_host.py` | Host demo script |
| `demo_rate_limit.py` | Rate limit test script |
