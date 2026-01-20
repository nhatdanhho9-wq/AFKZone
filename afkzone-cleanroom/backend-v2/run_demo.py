#!/usr/bin/env python3
"""
Quick test script to create session and run host agent.
"""
import asyncio
import json
import sys
import subprocess
import httpx

BASE_URL = "http://171.253.168.44:21121"
EMAIL = "demo@afkzone.io"
PASSWORD = "demo2026"
DEVICE_ID = "dev_cloud01"


async def main():
    print("=== AFKZone Phase 1 Demo ===")
    
    # Login
    print("\n1. Logging in...")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": EMAIL, "password": PASSWORD}
        )
        data = resp.json()
        if not data.get("ok"):
            print(f"Login failed: {data}")
            return
        token = data.get("access_token")
        print(f"   Token: {token[:30]}...")
    
    # Request session
    print(f"\n2. Requesting session for {DEVICE_ID}...")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/remote/request",
            headers={"Authorization": f"Bearer {token}"},
            json={"device_id": DEVICE_ID}
        )
        data = resp.json()
        if not data.get("ok"):
            print(f"Session request failed: {data}")
            return
        session_id = data.get("session", {}).get("id")
        print(f"   Session ID: {session_id}")
    
    print(f"\n3. Starting aiortc host agent...")
    print(f"   Run: python aiortc_host.py {session_id}")
    print("\n" + "=" * 50)
    
    # Run host agent
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "aiortc_host.py", session_id,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )
    
    try:
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            print(line.decode().strip())
    except KeyboardInterrupt:
        proc.terminate()
        print("\nStopped.")


if __name__ == "__main__":
    asyncio.run(main())
