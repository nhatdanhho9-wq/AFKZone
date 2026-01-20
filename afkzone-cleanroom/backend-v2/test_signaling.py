#!/usr/bin/env python3
"""Step-by-step test of aiortc host."""
import asyncio
import json
import httpx
import websockets

WS_URL = "ws://171.253.168.44:21121"
BASE_URL = "http://171.253.168.44:21121"


async def main():
    print("Step 1: Login")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": "demo@afkzone.io", "password": "demo2026"}
        )
        data = resp.json()
        token = data.get("access_token")
        print(f"  Token: {token[:30]}...")
    
    print("\nStep 2: Request session")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/remote/request",
            headers={"Authorization": f"Bearer {token}"},
            json={"device_id": "dev_cloud01"}
        )
        data = resp.json()
        session_id = data.get("session", {}).get("id")
        print(f"  Session: {session_id}")
    
    print("\nStep 3: Connect WS as host")
    ws_url = f"{WS_URL}/sessions/{session_id}/ws?role=host"
    print(f"  URL: {ws_url}")
    
    async with websockets.connect(ws_url) as ws:
        print("  WS connected!")
        
        # Send test SDP
        await ws.send(json.dumps({
            "type": "SDP_OFFER",
            "sdp": "v=0\r\no=test\r\n"
        }))
        print("  SDP_OFFER sent")
        
        # Send ICE
        await ws.send(json.dumps({
            "type": "ICE_CANDIDATE",
            "candidate": "candidate:1 1 UDP 2130706431 192.168.1.1 12345 typ host",
            "sdpMid": "0",
            "sdpMLineIndex": 0
        }))
        print("  ICE_CANDIDATE sent")
        
        # Wait for response
        print("\nStep 4: Waiting for messages (5 sec)...")
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            print(f"  Received: {msg}")
        except asyncio.TimeoutError:
            print("  No response (client not connected)")
        
        print("\n[OK] Signaling test complete!")


if __name__ == "__main__":
    asyncio.run(main())
