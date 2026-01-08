#!/usr/bin/env python3
"""
OpusD Signaling Demo - Host Script
===================================
Simulates a host device accepting a remote session.

Usage:
    python demo_host.py [device_id]

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
DEVICE_ID = sys.argv[1] if len(sys.argv) > 1 else "host-device-001"


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{ts}] HOST: {msg}")


async def main():
    log(f"Host device ID: {DEVICE_ID}")
    log("Waiting for incoming session...")
    
    # Poll for pending session (in real app, would be push notification)
    async with httpx.AsyncClient() as client:
        # Try to attach to pending session
        log("POST /sessions/host/attach")
        resp = await client.post(
            f"{BASE_URL}/sessions/host/attach",
            json={"host_device_id": DEVICE_ID}
        )
        
        if resp.status_code == 404:
            log("No pending session. Make sure controller runs first!")
            log("Retrying in 2s...")
            await asyncio.sleep(2)
            resp = await client.post(
                f"{BASE_URL}/sessions/host/attach",
                json={"host_device_id": DEVICE_ID}
            )
        
        if resp.status_code != 200:
            log(f"ERROR: {resp.status_code} - {resp.text}")
            return
        
        data = resp.json()
        session_id = data["session_id"]
        token = data["token"]
        ws_url = data["signaling_ws_url"]
        
        log(f"Attached to session: {session_id}")
        log(f"Token: {token[:20]}...")
    
    # Connect to WebSocket
    ws_full_url = f"ws://localhost:8081{ws_url}?token={token}"
    log(f"Connecting to WebSocket...")
    
    async with websockets.connect(ws_full_url) as ws:
        log("WebSocket connected!")
        
        # Wait for SDP offer
        log("Waiting for SDP offer from controller...")
        
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=60)
            data = json.loads(msg)
            log(f"Received: {data['type']} from {data['role']}")
            
            if data["type"] == "sdp_offer":
                log("SDP offer received! Processing...")
                
                # Send SDP answer
                sdp_answer = {
                    "type": "sdp_answer",
                    "session_id": session_id,
                    "role": "host",
                    "ts": datetime.now().isoformat(),
                    "payload": {
                        "type": "answer",
                        "sdp": "v=0\r\no=- 789012 2 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\n..."
                    }
                }
                
                log("Sending SDP answer...")
                await ws.send(json.dumps(sdp_answer))
                log("SDP answer sent!")
                
                # Wait for ICE from controller
                msg = await asyncio.wait_for(ws.recv(), timeout=10)
                data = json.loads(msg)
                log(f"Received: {data['type']} from {data['role']}")
                
                # Send ICE candidate
                ice_candidate = {
                    "type": "ice_candidate",
                    "session_id": session_id,
                    "role": "host",
                    "ts": datetime.now().isoformat(),
                    "payload": {
                        "candidate": "candidate:2 1 UDP 2130706430 192.168.1.200 54322 typ host",
                        "sdpMid": "0",
                        "sdpMLineIndex": 0
                    }
                }
                
                log("Sending ICE candidate...")
                await ws.send(json.dumps(ice_candidate))
                log("ICE candidate sent!")
                
                # Send control_ready
                await asyncio.sleep(0.5)
                control_ready = {
                    "type": "control_ready",
                    "session_id": session_id,
                    "role": "host",
                    "ts": datetime.now().isoformat(),
                    "payload": {}
                }
                
                log("Sending control_ready...")
                await ws.send(json.dumps(control_ready))
                log("🎉 control_ready sent! Session fully established!")
                
        except asyncio.TimeoutError:
            log("Timeout waiting for SDP offer.")
        
        # Keep connection open briefly
        await asyncio.sleep(2)
        log("Demo complete. Closing connection...")


if __name__ == "__main__":
    print("=" * 60)
    print("OpusD Signaling Demo - HOST")
    print("=" * 60)
    asyncio.run(main())
    print("=" * 60)
