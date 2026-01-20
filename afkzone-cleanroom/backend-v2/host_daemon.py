#!/usr/bin/env python3
"""
Persistent Host Agent Daemon for dev_cloud01
Monitors for incoming session requests and auto-connects as host.
"""
import asyncio
import json
import time
import httpx
import websockets

# Configuration
API_BASE = "http://127.0.0.1:21121"
WS_BASE = "ws://127.0.0.1:21121"
DEVICE_ID = "dev_cloud01"

# Credentials (demo user)
EMAIL = "demo@afkzone.io"
PASSWORD = "demo2026"

# Mock SDP
MOCK_SDP = """v=0
o=- 123456789 2 IN IP4 192.168.1.100
s=AFKZone Host Stream
t=0 0
a=group:BUNDLE 0
m=video 9 UDP/TLS/RTP/SAVPF 96 97
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
a=rtpmap:97 H264/90000
"""

MOCK_ICE = {
    "candidate": "candidate:1 1 UDP 2130706431 192.168.1.100 54321 typ host",
    "sdpMid": "0",
    "sdpMLineIndex": 0
}


class HostAgentDaemon:
    def __init__(self):
        self.token = None
        self.active_sessions = set()
        self.running = True
    
    async def login(self):
        """Login and get access token."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{API_BASE}/auth/login",
                json={"email": EMAIL, "password": PASSWORD}
            )
            data = resp.json()
            if data.get("ok"):
                self.token = data.get("access_token")
                print(f"[DAEMON] Logged in as {EMAIL}")
                return True
            print(f"[DAEMON] Login failed: {data}")
            return False
    
    async def send_heartbeat(self):
        """Send device heartbeat."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{API_BASE}/devices/{DEVICE_ID}/heartbeat",
                json={"status": "online"}
            )
            print(f"[DAEMON] Heartbeat: {resp.json()}")
    
    async def handle_session(self, session_id: str):
        """Handle a remote session as host."""
        if session_id in self.active_sessions:
            return
        
        self.active_sessions.add(session_id)
        ws_url = f"{WS_BASE}/sessions/{session_id}/ws?role=host&token={self.token}"
        
        print(f"[HOST] Connecting to session {session_id}...")
        
        try:
            async with websockets.connect(ws_url) as ws:
                print(f"[HOST] WS_CONNECT session_id={session_id} role=host timestamp={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
                
                # Send SDP_OFFER immediately
                await ws.send(json.dumps({
                    "type": "SDP_OFFER",
                    "sdp": MOCK_SDP
                }))
                print(f"[HOST] SDP_OFFER sent for session {session_id}")
                
                # Send ICE candidates
                await ws.send(json.dumps({
                    "type": "ICE_CANDIDATE",
                    **MOCK_ICE
                }))
                print(f"[HOST] ICE_CANDIDATE sent for session {session_id}")
                
                # Listen for messages
                while self.running:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=30)
                        data = json.loads(msg)
                        msg_type = data.get("type", "unknown")
                        print(f"[HOST] Received: {msg_type} for session {session_id}")
                        
                        if msg_type == "SDP_ANSWER":
                            print(f"[HOST] Got SDP_ANSWER - WebRTC negotiation complete!")
                            # Send connected state
                            await ws.send(json.dumps({
                                "type": "SESSION_STATE",
                                "state": "connected"
                            }))
                            
                        elif msg_type == "ICE_CANDIDATE":
                            print(f"[HOST] Got ICE from client, sending more candidates...")
                            await ws.send(json.dumps({
                                "type": "ICE_CANDIDATE",
                                "candidate": "candidate:2 1 UDP 1694498815 203.0.113.1 54322 typ srflx raddr 192.168.1.100 rport 54321",
                                "sdpMid": "0",
                                "sdpMLineIndex": 0
                            }))
                            
                        elif msg_type == "INPUT_EVENT":
                            print(f"[HOST] INPUT_EVENT received - would process input here")
                            
                    except asyncio.TimeoutError:
                        # Send keepalive
                        await ws.send(json.dumps({"type": "PING"}))
                        
        except Exception as e:
            print(f"[HOST] Session {session_id} error: {e}")
        finally:
            self.active_sessions.discard(session_id)
            print(f"[HOST] Session {session_id} ended")
    
    async def poll_pending_sessions(self):
        """Poll for new session requests targeting this device."""
        while self.running:
            try:
                async with httpx.AsyncClient() as client:
                    # Check for pending sessions via remote/pending
                    resp = await client.get(
                        f"{API_BASE}/remote/pending",
                        headers={"Authorization": f"Bearer {self.token}"}
                    )
                    data = resp.json()
                    
                    if data.get("ok"):
                        for session in data.get("requests", []):
                            if session.get("host_device_id") == DEVICE_ID:
                                session_id = session.get("request_id") or session.get("id")
                                if session_id and session_id not in self.active_sessions:
                                    asyncio.create_task(self.handle_session(session_id))
                                    
            except Exception as e:
                print(f"[DAEMON] Poll error: {e}")
            
            await asyncio.sleep(2)
    
    async def heartbeat_loop(self):
        """Send periodic heartbeats."""
        while self.running:
            await self.send_heartbeat()
            await asyncio.sleep(30)
    
    async def run(self):
        """Main daemon loop."""
        print(f"[DAEMON] Starting host agent for {DEVICE_ID}")
        
        if not await self.login():
            return
        
        await self.send_heartbeat()
        
        # Start background tasks
        asyncio.create_task(self.heartbeat_loop())
        asyncio.create_task(self.poll_pending_sessions())
        
        print(f"[DAEMON] Host agent ready. Waiting for sessions...")
        print(f"[DAEMON] To test: POST /remote/request {{\"device_id\":\"{DEVICE_ID}\"}}")
        
        # Keep running
        while self.running:
            await asyncio.sleep(1)


async def main():
    daemon = HostAgentDaemon()
    try:
        await daemon.run()
    except KeyboardInterrupt:
        print("\n[DAEMON] Shutting down...")
        daemon.running = False


if __name__ == "__main__":
    asyncio.run(main())
