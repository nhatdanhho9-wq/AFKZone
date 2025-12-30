#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests

# Test admin login
print("1. Testing admin login...")
login_response = requests.post("https://api.afkzone.cloud/admin/login", json={
    "username": "admin",
    "password": "admin123"
})

print(f"   Status: {login_response.status_code}")
if login_response.status_code != 200:
    print(f"   Error: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
print(f"   Token: {token[:50]}...")

# Test get orders
print("\n2. Testing GET /admin/orders...")
orders_response = requests.get(
    "https://api.afkzone.cloud/admin/orders",
    headers={"Authorization": f"Bearer {token}"}
)
print(f"   Status: {orders_response.status_code}")
if orders_response.status_code == 200:
    orders = orders_response.json().get("orders", [])
    print(f"   Found {len(orders)} orders")
    if orders:
        print(f"   First order: {orders[0]['trans_code']} - {orders[0]['status']}")
else:
    print(f"   Error: {orders_response.text}")

# Test complete order (with a pending one)
print("\n3. Testing POST /admin/orders/{trans_code}/complete...")
# Find first pending order
pending_order = None
if orders_response.status_code == 200:
    for order in orders_response.json().get("orders", []):
        if order['status'] == 'pending':
            pending_order = order['trans_code']
            break

if pending_order:
    print(f"   Trying to complete: {pending_order}")
    complete_response = requests.post(
        f"https://api.afkzone.cloud/admin/orders/{pending_order}/complete",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"   Status: {complete_response.status_code}")
    if complete_response.status_code == 200:
        result = complete_response.json()
        print(f"   Success: {result.get('success')}")
        print(f"   License: {result.get('license_key')}")
    else:
        print(f"   Error: {complete_response.text}")
else:
    print("   No pending orders to test")

# Check CORS headers
print("\n4. Checking CORS headers...")
import requests
response = requests.options("https://api.afkzone.cloud/admin/orders")
print(f"   Status: {response.status_code}")
print(f"   Headers: {dict(response.headers)}")

