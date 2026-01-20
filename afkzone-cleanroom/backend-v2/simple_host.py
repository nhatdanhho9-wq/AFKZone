#!/usr/bin/env python3
"""
Simple Host Agent - connects to a specific session and streams.
Usage: python3 simple_host.py <session_id>
"""
import asyncio
import json
import sys
import websockets

WS_BASE = "ws://127.0.0.1:21121"

MOCK_SDP_OFFER = """v=0
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

async def host_session(session_id: str):
    ws_url = f"{WS_BASE}/sessions/{session_id}/ws?role=host"
    print(f"[HOST] Connecting to: {ws_url}", flush=True)
    
    async with websockets.connect(ws_url) as ws:
        print(f"[HOST] WS_CONNECT session_id={session_id} role=host", flush=True)
        
        # Send SDP_OFFER immediately
        await ws.send(json.dumps({"type": "SDP_OFFER", "sdp": MOCK_SDP_OFFER}))
        print("[HOST] SDP_OFFER sent", flush=True)
        
        # Send ICE candidate
        await ws.send(json.dumps({
            "type": "ICE_CANDIDATE",
            "candidate": "candidate:1 1 UDP 2130706431 192.168.1.100 54321 typ host",
            "sdpMid": "0",
            "sdpMLineIndex": 0
        }))
        print("[HOST] ICE_CANDIDATE sent", flush=True)
        
        # Listen for messages
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=60)
                data = json.loads(msg)
                print(f"[HOST] Received: {data.get('type', 'unknown')}", flush=True)
                
                if data.get("type") == "SDP_ANSWER":
                    print("[HOST] Got SDP_ANSWER - connection ready!", flush=True)
                    await ws.send(json.dumps({"type": "SESSION_STATE", "state": "connected"}))
                    
                elif data.get("type") == "ICE_CANDIDATE":
                    print("[HOST] Got client ICE candidate", flush=True)
                    
            except asyncio.TimeoutError:
                print("[HOST] Keepalive...", flush=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 simple_host.py <session_id>")
        sys.exit(1)
    asyncio.run(host_session(sys.argv[1]))
