# Realtime Transport Choice (vNext)

Decision: **WebRTC-first** for MVP, with a relay fallback.

## Why WebRTC-first

- Fastest path to cross-platform media (Android/iOS/desktop) with NAT traversal.
- Mature congestion control, jitter buffering, and codec negotiation.
- Built-in encrypted media (SRTP) + data channels for control/file transfer.
- Existing TURN ecosystem for relay fallback.

## What “no RustDesk compatibility” means here

- We do **not** reuse RustDesk protocol formats or network stacks.
- We do **not** attempt to interoperate with RustDesk servers/clients.
- The stack is standard WebRTC primitives plus our own signaling/authz APIs.

## System components

- **Signaling service**: session creation + SDP exchange + ICE candidate exchange.
- **Relay (TURN-like)**: for NAT failure. Can start with standard TURN, later add managed relays.
- **Host agent**: exposes a “host session” endpoint and participates in signaling.
- **Controller client**: initiates sessions and sends input/control over data channel.

## Channel mapping

- **Video**: WebRTC media track(s) (H.264/VP8/VP9/AV1 per platform)
- **Audio** (optional): WebRTC audio track
- **Control/Input**: WebRTC DataChannel (`ordered=false` for low latency input)
- **File transfer**: WebRTC DataChannel or separate ordered channel (chunked + resumable)

## Authentication and authorization (authz)

- Control plane issues JWT + refresh token (account system).
- Signaling service verifies JWT and checks **entitlement** before starting a session.
- Host agent enforces local policy (permissions, unattended trust, allowlist).

### Entitlement checks

At session start, check:

- active subscription/license
- device quota (max devices / concurrent sessions)
- feature flags (e.g. file transfer allowed on plan)

## Signaling API (HTTP + WebSocket)

Two supported transport modes:

1. **WebSocket signaling** (recommended): fewer round trips, better for candidates.
2. **HTTP polling** fallback (optional).

### Core resources

- `POST /sessions/start` (controller -> signaling)
  - input: `{target_device_id, features_requested, region?}`
  - output: `{session_id, controller_token, signaling_ws_url}`

- `POST /sessions/host/attach` (host -> signaling)
  - input: `{host_device_id}`
  - output: `{session_id, host_token, signaling_ws_url}`

### WebSocket messages

All messages include:

- `session_id`
- `role`: `host | controller`
- `ts`

Message types:

- `sdp_offer` / `sdp_answer`
  - `{type, sdp}`
- `ice_candidate`
  - `{candidate, sdpMid, sdpMLineIndex}`
- `control_ready`
  - indicates data channel established and authz passed
- `error`
  - `{code, message}`

## Relay strategy

Phase 1 (MVP):

- Use standard TURN servers per region.
- Credentials minted by signaling service via short-lived tokens (TURN REST API).

Phase 2:

- Managed relays with regional routing + QoS.

## Security notes

- Pin signaling domain in clients.
- Use per-session short-lived tokens for signaling and TURN.
- Rate-limit session start to prevent abuse.
- Audit log for sessions (start/stop, IP, region, features).

