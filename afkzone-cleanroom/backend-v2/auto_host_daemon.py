#!/usr/bin/env python3
"""
AFKZone Host Agent Daemon
Auto-watches for new session requests and connects as host.

Run on VPS: python3 auto_host_daemon.py
"""
import asyncio
import json
import time
import httpx
import websockets
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:21121"
WS_URL = "ws://127.0.0.1:21121"
WATCH_DEVICE_ID = "dev_cloud01"
POLL_INTERVAL = 2  # seconds

# Demo user credentials (for testing)
EMAIL = "demo@afkzone.io"
PASSWORD = "demo2026"

# Track active sessions
active_sessions = set()


def log(msg):
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {msg}", flush=True)


async def login():
    """Login and get access token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": EMAIL, "password": PASSWORD}
        )
        data = resp.json()
        if data.get("ok"):
            return data.get("access_token")
    return None


async def get_pending_sessions(device_id):
    """Get pending session requests for device."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/sessions/pending?device_id={device_id}")
        data = resp.json()
        if data.get("ok"):
            return [r.get("session_id") for r in data.get("requests", [])]
    return []


async def handle_session(session_id: str, token: str):
    """Handle a session as host (simplified signaling)."""
    if session_id in active_sessions:
        return
    
    active_sessions.add(session_id)
    ws_url = f"{WS_URL}/sessions/{session_id}/ws?role=host&token={token}"
    
    log(f"HOST_CONNECT session_id={session_id}")
    
    try:
        async with websockets.connect(ws_url) as ws:
            log(f"WS_CONNECT session_id={session_id} role=host")
            
            # Send SDP_OFFER (mock for signaling test)
            sdp_offer = """v=0
o=- 123456789 2 IN IP4 192.168.1.100
s=AFKZone Host Stream
t=0 0
a=group:BUNDLE 0
m=video 9 UDP/TLS/RTP/SAVPF 96
c=IN IP4 0.0.0.0
a=rtcp:9 IN IP4 0.0.0.0
a=ice-ufrag:host1234
a=ice-pwd:hostpassword1234567890ab
a=fingerprint:sha-256 AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99
a=setup:actpass
a=mid:0
a=sendonly
a=rtcp-mux
a=rtpmap:96 VP8/90000
"""
            
            await ws.send(json.dumps({"type": "SDP_OFFER", "sdp": sdp_offer}))
            log(f"SDP_OFFER session_id={session_id}")
            
            # Send ICE candidates
            await ws.send(json.dumps({
                "type": "ICE_CANDIDATE",
                "candidate": "candidate:1 1 UDP 2130706431 192.168.1.100 54321 typ host",
                "sdpMid": "0",
                "sdpMLineIndex": 0
            }))
            log(f"ICE_CANDIDATE session_id={session_id}")
            
            # Listen for messages
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=30)
                    data = json.loads(msg)
                    msg_type = data.get("type")
                    log(f"RECEIVED session_id={session_id} type={msg_type}")
                    
                    if msg_type == "SDP_ANSWER":
                        log(f"SDP_ANSWER session_id={session_id} - CONNECTION READY")
                    elif msg_type == "ICE_CANDIDATE":
                        log(f"ICE_CANDIDATE session_id={session_id} from_client")
                    elif msg_type == "INPUT_EVENT":
                        payload = data.get("payload", {})
                        log(f"INPUT_EVENT session_id={session_id} type={payload.get('type')}")
                        
                except asyncio.TimeoutError:
                    # Keepalive
                    await ws.send(json.dumps({"type": "PING"}))
                    
    except websockets.exceptions.ConnectionClosed:
        log(f"WS_DISCONNECT session_id={session_id}")
    except Exception as e:
        log(f"ERROR session_id={session_id} error={e}")
    finally:
        active_sessions.discard(session_id)


async def poll_loop(token: str):
    """Poll for new sessions and handle them."""
    log(f"DAEMON_START watching device_id={WATCH_DEVICE_ID}")
    
    while True:
        try:
            pending = await get_pending_sessions(WATCH_DEVICE_ID)
            for session_id in pending:
                if session_id not in active_sessions:
                    log(f"NEW_SESSION session_id={session_id} device_id={WATCH_DEVICE_ID}")
                    asyncio.create_task(handle_session(session_id, token))
        except Exception as e:
            log(f"POLL_ERROR error={e}")
        
        await asyncio.sleep(POLL_INTERVAL)


async def main():
    log("AFKZone Auto Host Daemon starting...")
    
    # Login
    token = await login()
    if not token:
        log("LOGIN_FAILED - exiting")
        return
    log("LOGIN_OK")
    
    # Start polling
    await poll_loop(token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDaemon stopped.")
