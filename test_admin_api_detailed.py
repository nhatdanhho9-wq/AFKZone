#!/usr/bin/env python3
"""Detailed admin API endpoint test"""
import requests
import json

API_BASE = "https://api.afkzone.cloud"

# Login
login_resp = requests.post(f"{API_BASE}/admin/login", json={
    "username": "admin",
    "password": "afk_4nA3UWW1XUFKlqPOvnVR6Q"
})
token = login_resp.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

endpoints = [
    "/admin/dashboard/stats",
    "/admin/licenses/all",
    "/admin/orders",
    "/admin/products",
    "/admin/tiers",
    "/admin/devices/detailed",
    "/admin/connections",
    "/admin/notifications",
    "/admin/analytics/revenue",
    "/health"
]

for ep in endpoints:
    print(f"\n{'='*60}")
    print(f"ENDPOINT: {ep}")
    print('='*60)
    try:
        resp = requests.get(f"{API_BASE}{ep}", headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        # Pretty print first 500 chars
        pretty = json.dumps(data, indent=2, ensure_ascii=False)[:500]
        print(f"Response:\n{pretty}")
    except Exception as e:
        print(f"ERROR: {e}")
