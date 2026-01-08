#!/usr/bin/env python3
"""
OpusD Signaling Demo - Controller Script
=========================================
Simulates a controller initiating a remote session.

Usage:
    python demo_controller.py [target_device_id]

Requirements:
    pip install httpx websockets
"""

import asyncio
import json
import sys
from datetime import datetime

try:
    import httpx
    import websockets
except ImportError:
    print("ERROR: Install dependencies first:")
    print("  pip install httpx websockets")
    sys.exit(1)

# Configuration
BASE_URL = "http://localhost:8081"
TARGET_DEVICE_ID = sys.argv[1] if len(sys.argv) > 1 else "host-device-001"


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{ts}] CONTROLLER: {msg}")


async def main():
    log(f"Starting session for target device: {TARGET_DEVICE_ID}")
    
    # Step 1: Create session
    async with httpx.AsyncClient() as client:
        log("POST /sessions/start")
        resp = await client.post(
            f"{BASE_URL}/sessions/start",
            json={
                "target_device_id": TARGET_DEVICE_ID,
                "features_requested": ["remote_desktop", "file_transfer"],
                "region": "vn"
            }
        )
        
        if resp.status_code != 200:
            log(f"ERROR: {resp.status_code} - {resp.text}")
            return
        
        data = resp.json()
        session_id = data["session_id"]
        token = data["token"]
        ws_url = data["signaling_ws_url"]
        
        log(f"Session created: {session_id}")
        log(f"Token: {token[:20]}...")
        log(f"WS URL: {ws_url}")
        
        # Step 2: Get TURN credentials
        log("GET /sessions/{id}/turn-credentials")
        turn_resp = await client.get(f"{BASE_URL}/sessions/{session_id}/turn-credentials")
        if turn_resp.status_code == 200:
            turn_creds = turn_resp.json()
            log(f"TURN credentials received:")
            log(f"  URLs: {turn_creds['urls']}")
            log(f"  Username: {turn_creds['username']}")
            log(f"  TTL: {turn_creds['ttl']}s")
    
    # Step 3: Connect to WebSocket
    ws_full_url = f"ws://localhost:8081{ws_url}?token={token}"
    log(f"Connecting to WebSocket...")
    
    async with websockets.connect(ws_full_url) as ws:
        log("WebSocket connected!")
        
        # Wait a moment for host to connect
        log("Waiting 3s for host to connect...")
        await asyncio.sleep(3)
        
        # Step 4: Send SDP offer
        sdp_offer = {
            "type": "sdp_offer",
            "session_id": session_id,
            "role": "controller",
            "ts": datetime.now().isoformat(),
            "payload": {
                "type": "offer",
                "sdp": "v=0\r\no=- 123456 2 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\n..."
            }
        }
        
        log("Sending SDP offer...")
        await ws.send(json.dumps(sdp_offer))
        log("SDP offer sent!")
        
        # Step 5: Wait for SDP answer
        log("Waiting for SDP answer...")
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=30)
            data = json.loads(msg)
            log(f"Received: {data['type']} from {data['role']}")
            
            if data["type"] == "sdp_answer":
                log("SDP answer received! Peer connection can be established.")
            
            # Step 6: Send ICE candidates
            ice_candidate = {
                "type": "ice_candidate",
                "session_id": session_id,
                "role": "controller",
                "ts": datetime.now().isoformat(),
                "payload": {
                    "candidate": "candidate:1 1 UDP 2130706431 192.168.1.100 54321 typ host",
                    "sdpMid": "0",
                    "sdpMLineIndex": 0
                }
            }
            
            log("Sending ICE candidate...")
            await ws.send(json.dumps(ice_candidate))
            log("ICE candidate sent!")
            
            # Wait for ICE from host
            msg = await asyncio.wait_for(ws.recv(), timeout=10)
            data = json.loads(msg)
            log(f"Received: {data['type']} from {data['role']}")
            
            # Wait for control_ready
            log("Waiting for control_ready...")
            msg = await asyncio.wait_for(ws.recv(), timeout=10)
            data = json.loads(msg)
            
            if data["type"] == "control_ready":
                log("🎉 control_ready received! Session fully established!")
            else:
                log(f"Received: {data['type']}")
            
        except asyncio.TimeoutError:
            log("Timeout waiting for response. Host may not be connected.")
        
        log("Demo complete. Closing connection...")


if __name__ == "__main__":
    print("=" * 60)
    print("OpusD Signaling Demo - CONTROLLER")
    print("=" * 60)
    asyncio.run(main())
    print("=" * 60)
