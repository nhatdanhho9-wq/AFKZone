#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests

# Check order 62 first
response = requests.get("https://api.afkzone.cloud/payment/bank/status?trans_code=AFKPRO2251230006")
print(f"Order 62 status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Trans code: {data['trans_code']}")
    print(f"Status: {data['status']}")
    print(f"Amount: {data['amount']}")
    
    if data['status'] == 'success':
        print(f"Already completed! License: {data['license_key']}")
        exit(0)
else:
    print(f"Error: {response.text}")
    exit(1)

# Login and complete
login_response = requests.post("https://api.afkzone.cloud/admin/login", json={
    "username": "admin",
    "password": "admin123"
})

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print("\nLogin successful, completing order...")
    
    complete_response = requests.post(
        "https://api.afkzone.cloud/admin/orders/AFKPRO2251230006/complete",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"\nComplete status: {complete_response.status_code}")
    if complete_response.status_code == 200:
        result = complete_response.json()
        print(f"Success: {result.get('success')}")
        print(f"License: {result.get('license_key')}")
        print(f"Tier: {result.get('tier')}")
        print(f"Duration: {result.get('duration_days')} days")
    else:
        print(f"Error: {complete_response.text}")
else:
    print(f"Login failed: {login_response.status_code}")

