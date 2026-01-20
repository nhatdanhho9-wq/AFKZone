#!/usr/bin/env python3
"""
AFKZone Signaling Test Suite
Tests WebSocket signaling flow for Phase 1 integration.
"""
import asyncio
import json
import sys
import httpx
import websockets

BASE_URL = "http://171.253.168.44:21121"
WS_URL = "ws://171.253.168.44:21121"

# Test credentials
EMAIL = "demo@afkzone.io"
PASSWORD = "demo2026"
DEVICE_ID = "dev_cloud01"


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


async def request_session(token: str, device_id: str):
    """Request a remote session."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/remote/request",
            headers={"Authorization": f"Bearer {token}"},
            json={"device_id": device_id}
        )
        data = resp.json()
        if data.get("ok"):
            return data.get("session", {}).get("id")
    return None


async def test_host_signaling(session_id: str):
    """Test host-side signaling flow."""
    ws_url = f"{WS_URL}/sessions/{session_id}/ws?role=host"
    print(f"\n[HOST TEST] Connecting to: {ws_url}")
    
    async with websockets.connect(ws_url) as ws:
        print("[HOST TEST] ✅ WS_CONNECT successful")
        
        # Send SDP_OFFER
        await ws.send(json.dumps({
            "type": "SDP_OFFER",
            "sdp": "v=0\r\no=- 123 2 IN IP4 127.0.0.1\r\ns=Test\r\nt=0 0\r\na=group:BUNDLE 0\r\nm=video 9 UDP/TLS/RTP/SAVPF 96\r\n"
        }))
        print("[HOST TEST] ✅ SDP_OFFER sent")
        
        # Send ICE_CANDIDATE
        await ws.send(json.dumps({
            "type": "ICE_CANDIDATE",
            "candidate": "candidate:1 1 UDP 2130706431 192.168.1.1 12345 typ host",
            "sdpMid": "0",
            "sdpMLineIndex": 0
        }))
        print("[HOST TEST] ✅ ICE_CANDIDATE sent")
        
        # Wait for response (or timeout)
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            print(f"[HOST TEST] Received: {data.get('type')}")
        except asyncio.TimeoutError:
            print("[HOST TEST] No response (expected if no client connected)")
        
        return True


async def test_client_signaling(session_id: str, token: str):
    """Test client-side signaling flow."""
    ws_url = f"{WS_URL}/sessions/{session_id}/ws?role=client&token={token}"
    print(f"\n[CLIENT TEST] Connecting to: {ws_url}")
    
    async with websockets.connect(ws_url) as ws:
        print("[CLIENT TEST] ✅ WS_CONNECT successful")
        
        # Wait for SDP_OFFER from host
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            print(f"[CLIENT TEST] Received: {data.get('type')}")
            
            if data.get("type") == "SDP_OFFER":
                # Send SDP_ANSWER
                await ws.send(json.dumps({
                    "type": "SDP_ANSWER",
                    "sdp": "v=0\r\no=- 456 2 IN IP4 127.0.0.1\r\ns=Test Answer\r\n"
                }))
                print("[CLIENT TEST] ✅ SDP_ANSWER sent")
                
        except asyncio.TimeoutError:
            print("[CLIENT TEST] No SDP_OFFER received (host not connected)")
        
        return True


async def test_device_control(device_id: str, token: str):
    """Test device control WebSocket."""
    ws_url = f"{WS_URL}/sessions/devices/{device_id}/control?token={token}"
    print(f"\n[CONTROL TEST] Connecting to: {ws_url}")
    
    async with websockets.connect(ws_url) as ws:
        print("[CONTROL TEST] ✅ DEVICE_CONTROL_CONNECT successful")
        
        # Send heartbeat
        await ws.send(json.dumps({"type": "HEARTBEAT"}))
        print("[CONTROL TEST] ✅ HEARTBEAT sent")
        
        # Wait for ACK
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            if data.get("type") == "HEARTBEAT_ACK":
                print(f"[CONTROL TEST] ✅ HEARTBEAT_ACK received: {data.get('server_time')}")
            elif data.get("type") == "REMOTE_REQUESTED":
                print(f"[CONTROL TEST] ✅ REMOTE_REQUESTED: {data.get('session_id')}")
        except asyncio.TimeoutError:
            print("[CONTROL TEST] No response (timeout)")
        
        return True


async def test_pending_sessions(device_id: str):
    """Test pending sessions polling endpoint."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/sessions/pending?device_id={device_id}")
        data = resp.json()
        print(f"\n[PENDING TEST] GET /sessions/pending?device_id={device_id}")
        print(f"[PENDING TEST] Response: {json.dumps(data, indent=2)}")
        return data.get("ok", False)


async def run_all_tests():
    """Run all signaling tests."""
    print("=" * 60)
    print("AFKZone Signaling Test Suite")
    print("=" * 60)
    
    # Login
    print("\n[AUTH] Logging in...")
    token = await login()
    if not token:
        print("[AUTH] ❌ Login failed")
        return
    print("[AUTH] ✅ Login successful")
    
    # Request session
    print("\n[SESSION] Requesting session...")
    session_id = await request_session(token, DEVICE_ID)
    if not session_id:
        print("[SESSION] ❌ Session request failed")
        return
    print(f"[SESSION] ✅ Session created: {session_id}")
    
    # Test device control
    await test_device_control(DEVICE_ID, token)
    
    # Test pending sessions
    await test_pending_sessions(DEVICE_ID)
    
    # Test host signaling
    await test_host_signaling(session_id)
    
    # Test client signaling (in parallel with host)
    # Note: For full test, run host and client simultaneously
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
