#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests

# Check order 60
response = requests.get("https://api.afkzone.cloud/payment/bank/status?trans_code=AFKPRO2251230005")
print(f"Order 60 status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Trans code: {data['trans_code']}")
    print(f"Status: {data['status']}")
    print(f"Amount: {data['amount']}")
else:
    print(f"Error: {response.text}")

# Try to complete it
login_response = requests.post("https://api.afkzone.cloud/admin/login", json={
    "username": "admin",
    "password": "admin123"
})

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print("\nLogin successful, trying to complete...")
    
    complete_response = requests.post(
        "https://api.afkzone.cloud/admin/orders/AFKPRO2251230005/complete",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"Complete status: {complete_response.status_code}")
    if complete_response.status_code == 200:
        result = complete_response.json()
        print(f"Success: {result.get('success')}")
        print(f"License: {result.get('license_key')}")
    else:
        print(f"Error: {complete_response.text}")

