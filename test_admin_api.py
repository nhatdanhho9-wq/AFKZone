#!/usr/bin/env python3
"""Test admin API endpoints"""
import requests
import json

API_BASE = "https://api.afkzone.cloud"

# Login
print("=== Logging in ===")
login_resp = requests.post(f"{API_BASE}/admin/login", json={
    "username": "admin",
    "password": "afk_4nA3UWW1XUFKlqPOvnVR6Q"
})
print(f"Login status: {login_resp.status_code}")
print(f"Login response: {login_resp.text[:200]}")

if login_resp.status_code != 200:
    print("Login failed!")
    exit(1)

token = login_resp.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Test endpoints
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

print("\n=== Testing Endpoints ===")
for ep in endpoints:
    try:
        resp = requests.get(f"{API_BASE}{ep}", headers=headers, timeout=10)
        data = resp.json() if resp.status_code == 200 else {}
        fields = list(data.keys())[:5] if isinstance(data, dict) else ["array"]
        print(f"{ep}: {resp.status_code} - Fields: {fields}")
    except Exception as e:
        print(f"{ep}: ERROR - {e}")
