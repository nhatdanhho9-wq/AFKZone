# AFKZone Remote Backend v2

Complete backend implementation based on API Spec JSON.

## Quick Start

```bash
cd backend-v2
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 21121 --reload
```

## Docker

```bash
docker-compose up -d
```

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/register | Register with email, password, username |
| POST | /auth/login | Login with email + password |
| POST | /auth/refresh | Refresh access token |

### User
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /user/profile | Get profile |
| PATCH | /user/profile | Update profile |

### Devices
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /devices | List devices |
| POST | /devices/{id}/reboot | Reboot device |
| POST | /devices/{id}/stop | Stop device |

### Trusted
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /trusted/devices | List trusted |
| POST | /trusted/add | Add trusted |
| POST | /trusted/revoke | Revoke trusted |

### Remote
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /remote/request | Request session |
| GET | /remote/session/{id} | Get session details |
| POST | /remote/password/verify | Verify password |

### Plans
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /plans | List plans |

### Notifications
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /user/notifications | List notifications |
| POST | /user/notifications/{id}/read | Mark read |

---

## Curl Examples

### Register
```bash
curl -X POST http://171.253.168.44:21121/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret123","username":"gamer01"}'
```

### Login
```bash
curl -X POST http://171.253.168.44:21121/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret123"}'
```

### Get Devices (with token)
```bash
curl http://171.253.168.44:21121/devices \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Get Profile
```bash
curl http://171.253.168.44:21121/user/profile \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Get Plans (no auth)
```bash
curl http://171.253.168.44:21121/plans
```

---

## UI Screen Mapping

| App Screen | API Endpoint |
|------------|--------------|
| Login (ESTABLISH LINK) | POST /auth/login `{email, password}` |
| Register (CREATE ACCOUNT) | POST /auth/register `{email, password, username}` |
| Devices (COMMAND CENTER) | GET /devices |
| Device Reboot | POST /devices/{id}/reboot |
| Device Stop | POST /devices/{id}/stop |
| News (SYSTEM INTEL) | GET /user/notifications |
| Store | GET /plans |
| Profile | GET /user/profile |
| Remote Session | POST /remote/request → GET /remote/session/{id} |

---

## Response Format

### Success
```json
{
  "ok": true,
  "user": {...},
  "access_token": "...",
  "refresh_token": "..."
}
```

### Error
```json
{
  "ok": false,
  "error_code": "INVALID_CREDENTIALS",
  "message": "Invalid email or password"
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| EMAIL_EXISTS | Email already registered |
| USERNAME_EXISTS | Username already taken |
| WEAK_PASSWORD | Password too short |
| INVALID_CREDENTIALS | Wrong email/password |
| UNAUTHORIZED | Missing/invalid auth |
| TOKEN_EXPIRED | Access token expired |
| DEVICE_OFFLINE | Device is offline |
| NOT_OWNER | Not device owner |
| DEVICE_NOT_FOUND | Device not found |
| SESSION_NOT_FOUND | Session not found |
| PASSWORD_REQUIRED | Device requires password |
| INVALID_PASSWORD | Wrong device password |
| TRUST_REQUIRED | Need trust or password |
