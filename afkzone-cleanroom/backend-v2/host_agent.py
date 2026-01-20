#!/usr/bin/env python3
"""
Simulated Host Agent - connects to WS as host and sends SDP_OFFER
Run this on VPS to act as a host device.
"""
import asyncio
import json
import websockets
import sys

# Configuration
API_BASE = "http://127.0.0.1:21121"
WS_BASE = "ws://127.0.0.1:21121"

# Simulated SDP offer
MOCK_SDP_OFFER = """v=0
o=- 123456789 2 IN IP4 127.0.0.1
s=-
t=0 0
a=group:BUNDLE 0
m=video 9 UDP/TLS/RTP/SAVPF 96
c=IN IP4 0.0.0.0
a=rtcp:9 IN IP4 0.0.0.0
a=ice-ufrag:abcd
a=ice-pwd:efghijklmnopqrstuvwx
a=fingerprint:sha-256 00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF
a=setup:actpass
a=mid:0
a=sendonly
a=rtcp-mux
a=rtpmap:96 VP8/90000
"""


async def host_agent(session_id: str, token: str = ""):
    """Connect as host and handle signaling."""
    ws_url = f"{WS_BASE}/sessions/{session_id}/ws?role=host&token={token}"
    print(f"[HOST] Connecting to: {ws_url}")
    
    try:
        async with websockets.connect(ws_url) as ws:
            print(f"[HOST] Connected! Waiting for client...")
            
            # Send initial host ready message
            await ws.send(json.dumps({
                "type": "HOST_READY",
                "device_id": "dev_cloud01"
            }))
            print("[HOST] Sent HOST_READY")
            
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=30)
                    data = json.loads(msg)
                    msg_type = data.get("type", "unknown")
                    print(f"[HOST] Received: {msg_type}")
                    
                    if msg_type == "SDP_OFFER":
                        # Client sent offer, we respond with answer
                        print("[HOST] Got SDP_OFFER from client, sending SDP_ANSWER...")
                        await ws.send(json.dumps({
                            "type": "SDP_ANSWER",
                            "sdp": MOCK_SDP_OFFER.replace("sendonly", "recvonly")
                        }))
                        print("[HOST] Sent SDP_ANSWER")
                        
                    elif msg_type == "ICE_CANDIDATE":
                        # Echo back a candidate
                        print("[HOST] Got ICE_CANDIDATE, sending our candidate...")
                        await ws.send(json.dumps({
                            "type": "ICE_CANDIDATE",
                            "candidate": "candidate:1 1 UDP 2130706431 192.168.1.1 12345 typ host",
                            "sdpMid": "0",
                            "sdpMLineIndex": 0
                        }))
                        
                    elif msg_type == "SESSION_STATE":
                        state = data.get("state")
                        print(f"[HOST] Session state: {state}")
                        if state == "connected":
                            print("[HOST] Session connected! Streaming would start here.")
                            
                except asyncio.TimeoutError:
                    # Send heartbeat / SDP offer to initiate
                    print("[HOST] Timeout, sending SDP_OFFER to initiate...")
                    await ws.send(json.dumps({
                        "type": "SDP_OFFER",
                        "sdp": MOCK_SDP_OFFER
                    }))
                    print("[HOST] Sent SDP_OFFER")
                    
    except Exception as e:
        print(f"[HOST] Error: {e}")


async def main():
    if len(sys.argv) < 2:
        print("Usage: python host_agent.py <session_id> [token]")
        print("Example: python host_agent.py abc123xyz")
        return
    
    session_id = sys.argv[1]
    token = sys.argv[2] if len(sys.argv) > 2 else ""
    
    await host_agent(session_id, token)


if __name__ == "__main__":
    asyncio.run(main())
