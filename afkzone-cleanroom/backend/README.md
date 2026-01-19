# AFKZone Backend (Clean-Room)

FastAPI backend for AFKZone remote control system.

## Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 21121 --reload
```

## Endpoints

See `../contracts/api_spec.md` for full API documentation.

### Auth
- POST /auth/login
- POST /auth/register

### Devices
- GET /devices
- POST /devices/register
- POST /devices/{id}/heartbeat
- POST /devices/{id}/reboot
- POST /devices/{id}/stop
- GET /devices/{id}/status

### Remote
- POST /remote/request
- GET /remote/pending
- POST /remote/approve
- POST /remote/deny
- POST /remote/host-ready/{request_id}
- POST /remote/password/verify

### Trusted
- POST /trusted/request
- POST /trusted/approve
- GET /trusted/list
- DELETE /trusted/{id}

### Sessions
- GET /sessions/{id}/status
- POST /sessions/{id}/stats
- POST /sessions/{id}/input-control
- POST /sessions/{id}/disconnect
- GET /sessions/{id}/turn-credentials
- WS /sessions/{id}/ws
