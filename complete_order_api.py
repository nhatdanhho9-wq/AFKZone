#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests

# Login to get token
login_response = requests.post("https://api.afkzone.cloud/admin/login", json={
    "username": "admin",
    "password": "admin123"
})

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print("Login successful")
    
    # Complete order
    complete_response = requests.post(
        "https://api.afkzone.cloud/admin/orders/AFKPRO2251230003/complete",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"\nStatus: {complete_response.status_code}")
    result = complete_response.json()
    print(f"Success: {result.get('success')}")
    print(f"License: {result.get('license_key')}")
    print(f"Tier: {result.get('tier')}")
    print(f"Duration: {result.get('duration_days')} days")
else:
    print(f"Login failed: {login_response.status_code}")
    print(login_response.text)
