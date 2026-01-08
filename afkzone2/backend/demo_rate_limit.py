#!/usr/bin/env python3
"""
OpusD Signaling Demo - Rate Limit Test
=======================================
Tests rate limiting by spamming session start requests.

Usage:
    python demo_rate_limit.py

Requirements:
    pip install httpx
"""

import asyncio
import sys
from datetime import datetime

try:
    import httpx
except ImportError:
    print("ERROR: Install dependencies first:")
    print("  pip install httpx")
    sys.exit(1)

# Configuration
BASE_URL = "http://localhost:8081"
NUM_REQUESTS = 15
DELAY_MS = 100  # 100ms between requests


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{ts}] RATE_LIMIT_TEST: {msg}")


async def main():
    log(f"Testing rate limit: {NUM_REQUESTS} requests with {DELAY_MS}ms delay")
    log("=" * 50)
    
    success_count = 0
    blocked_count = 0
    
    async with httpx.AsyncClient() as client:
        for i in range(NUM_REQUESTS):
            try:
                resp = await client.post(
                    f"{BASE_URL}/sessions/start",
                    json={
                        "target_device_id": f"rate-limit-test-{i}",
                        "features_requested": [],
                        "region": "default"
                    }
                )
                
                if resp.status_code == 200:
                    success_count += 1
                    log(f"Request {i+1:2d}: ✅ 200 OK (session created)")
                elif resp.status_code == 429:
                    blocked_count += 1
                    log(f"Request {i+1:2d}: 🚫 429 RATE LIMITED")
                else:
                    log(f"Request {i+1:2d}: ⚠️  {resp.status_code} - {resp.text[:50]}")
                    
            except Exception as e:
                log(f"Request {i+1:2d}: ❌ ERROR - {e}")
            
            await asyncio.sleep(DELAY_MS / 1000)
    
    log("=" * 50)
    log(f"Results: {success_count} success, {blocked_count} rate limited")
    
    if blocked_count > 0:
        log("✅ Rate limiting is WORKING!")
    else:
        log("⚠️  Rate limiting not triggered (skeleton mode or limit too high)")


if __name__ == "__main__":
    print("=" * 60)
    print("OpusD Signaling Demo - RATE LIMIT TEST")
    print("=" * 60)
    asyncio.run(main())
    print("=" * 60)
