# API Contract (MVP) - Clean-Room Specification

## Base URL
```
https://api.afkzone.io/v1
```

## Authentication
All endpoints require Bearer token in header:
```
Authorization: Bearer {access_token}
```

---

## Endpoints

### 1. POST /remote/request

Request remote access to a target device.

**Request:**
```json
{
  "target_device_id": "string",
  "requester_device_id": "string"
}
```

**Response (201 Created):**
```json
{
  "request_id": "uuid",
  "status": "pending",
  "created_at": "ISO8601",
  "expires_at": "ISO8601"
}
```

**Headers:**
| Header | Value |
|--------|-------|
| Content-Type | application/json |
| X-Request-Id | UUID (for tracing) |

---

### 2. GET /remote/pending

Get list of pending remote requests for current user's devices.

**Query Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| device_id | string | No | Filter by specific device |

**Response (200 OK):**
```json
{
  "requests": [
    {
      "request_id": "uuid",
      "requester_device_id": "string",
      "requester_device_name": "string",
      "target_device_id": "string",
      "status": "pending",
      "created_at": "ISO8601",
      "expires_at": "ISO8601"
    }
  ]
}
```

---

### 3. POST /remote/approve

Approve a pending remote request.

**Request:**
```json
{
  "request_id": "uuid"
}
```

**Response (200 OK):**
```json
{
  "request_id": "uuid",
  "status": "wait_host_ready",
  "signaling_ws_url": "wss://signaling.afkzone.io/ws/{session_id}"
}
```

**Response (403 Forbidden):**
```json
{
  "error": "REQUEST_DENIED",
  "message": "Request was denied by target"
}
```

---

### 4. POST /remote/deny

Deny a pending remote request.

**Request:**
```json
{
  "request_id": "uuid"
}
```

**Response (200 OK):**
```json
{
  "request_id": "uuid",
  "status": "denied"
}
```

---

### 5. POST /remote/host-ready/{request_id}

Signal that host device has started screen capture and is ready for WebRTC.

**Path Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| request_id | uuid | The approved request ID |

**Response (200 OK):**
```json
{
  "session_id": "uuid",
  "host_token": "string",
  "signaling_ws_url": "wss://signaling.afkzone.io/ws/{session_id}",
  "turn_credentials_url": "/sessions/{session_id}/turn-credentials"
}
```

---

### 6. GET /sessions/{session_id}/turn-credentials

Get TURN server credentials for WebRTC connection.

**Path Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| session_id | uuid | Active session ID |

**Response (200 OK):**
```json
{
  "ice_servers": [
    {
      "urls": ["stun:stun.afkzone.io:3478"],
      "username": "",
      "credential": ""
    },
    {
      "urls": ["turn:turn.afkzone.io:3478?transport=udp"],
      "username": "generated_username",
      "credential": "generated_credential"
    }
  ],
  "ttl": 86400
}
```

---

## Trusted Device Management (NEW)

### 7. POST /trusted/request

Request to add a device to trusted list (requires approval from target device owner).

**Request:**
```json
{
  "target_device_id": "string",
  "requester_device_id": "string",
  "label": "string (optional)"
}
```

**Response (201 Created):**
```json
{
  "trust_request_id": "uuid",
  "status": "pending",
  "created_at": "ISO8601",
  "expires_at": "ISO8601"
}
```

**Audit Log:** `TRUST_REQUEST device_id={target} requester={requester}`

---

### 8. POST /trusted/approve

Approve a pending trust request.

**Request:**
```json
{
  "trust_request_id": "uuid",
  "allow_input_control": true,
  "allow_file_transfer": false
}
```

**Response (200 OK):**
```json
{
  "trust_id": "uuid",
  "status": "approved",
  "permissions": {
    "allow_input_control": true,
    "allow_file_transfer": false
  }
}
```

**Response (403 Forbidden):**
```json
{
  "error": "TRUST_DENIED",
  "message": "Trust request was denied"
}
```

**Audit Log:** `TRUST_APPROVE trust_id={trust_id} device_id={target} permissions={...}`

---

### 9. GET /trusted/list

Get list of trusted devices for current user.

**Query Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| device_id | string | No | Filter by specific device |
| direction | string | No | "inbound" or "outbound" |

**Response (200 OK):**
```json
{
  "trusted_devices": [
    {
      "trust_id": "uuid",
      "device_id": "string",
      "device_name": "string",
      "direction": "inbound|outbound",
      "permissions": {
        "allow_input_control": true,
        "allow_file_transfer": false
      },
      "created_at": "ISO8601",
      "last_used_at": "ISO8601"
    }
  ]
}
```

---

### 10. DELETE /trusted/{trust_id}

Remove a device from trusted list.

**Path Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| trust_id | uuid | The trust relationship ID |

**Response (200 OK):**
```json
{
  "trust_id": "uuid",
  "status": "revoked"
}
```

**Audit Log:** `TRUST_REVOKE trust_id={trust_id} revoked_by={account_id}`

---

## Password Verification (NEW)

### 11. POST /remote/password/verify

Verify password for remote access (alternative to approval flow).

**Request:**
```json
{
  "target_device_id": "string",
  "password": "string"
}
```

**Response (200 OK):**
```json
{
  "verified": true,
  "session_id": "uuid",
  "signaling_ws_url": "wss://signaling.afkzone.io/ws/{session_id}",
  "controller_token": "string"
}
```

**Response (401 Unauthorized):**
```json
{
  "error": "INVALID_PASSWORD",
  "message": "Password incorrect"
}
```

**Response (403 Forbidden):**
```json
{
  "error": "PASSWORD_DISABLED",
  "message": "Password access not enabled for this device"
}
```

**Audit Log:** `PASSWORD_VERIFY device_id={target} success={true|false} ip={client_ip}`

---

## Audit Logging

All sensitive operations produce audit logs with the following format:

```
{ACTION} {key}={value} ... timestamp={ISO8601}
```

| Action | Description |
|--------|-------------|
| TRUST_REQUEST | Trust request created |
| TRUST_APPROVE | Trust approved with permissions |
| TRUST_DENY | Trust request denied |
| TRUST_REVOKE | Trust relationship revoked |
| PASSWORD_VERIFY | Password verification attempt |
| INPUT_CONTROL_START | Input control enabled in session |
| INPUT_CONTROL_STOP | Input control disabled in session |

---

## Error Codes

All errors return a JSON body with `error` and `message` fields, plus `X-Error-Code` header.

| HTTP Status | X-Error-Code | Description |
|-------------|--------------|-------------|
| 400 | INVALID_REQUEST | Malformed request body |
| 401 | UNAUTHORIZED | Missing or invalid token |
| 401 | INVALID_PASSWORD | Password incorrect |
| 403 | REQUEST_DENIED | Request denied by target |
| 403 | TRUST_DENIED | Trust request denied |
| 403 | PASSWORD_DISABLED | Password access not enabled |
| 403 | NOT_TARGET_DEVICE | Only target device can approve |
| 404 | SESSION_EXPIRED | Session no longer valid |
| 404 | TARGET_OFFLINE | Target device not connected |
| 404 | REQUEST_NOT_FOUND | Request ID not found |
| 404 | TRUST_NOT_FOUND | Trust ID not found |
| 410 | HOST_ATTACH_DEPRECATED | Legacy endpoint removed |
| 429 | RATE_LIMITED | Too many requests |
| 503 | HOST_NOT_READY | Host still initializing capture |
| 503 | TURN_UNAVAILABLE | TURN service unavailable |

**Error Response Format:**
```json
{
  "error": "ERROR_CODE",
  "message": "Human readable message",
  "details": {}
}
```

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| POST /remote/request | 10/minute per user |
| GET /remote/pending | 60/minute per user |
| POST /remote/approve | 10/minute per device |
| POST /remote/password/verify | 5/minute per IP |
| POST /trusted/request | 10/minute per user |

---

## Versioning

API version is included in URL path (`/v1/`). Breaking changes require new version.

| Version | Status |
|---------|--------|
| v1 | Current (MVP) |

