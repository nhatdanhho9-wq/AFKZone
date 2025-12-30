#!/usr/bin/env python3
"""Manually complete order via internal API call"""
import requests
import secrets
from datetime import datetime, timedelta

trans_code = "AFKPRO2251230002"

# Simulate webhook payload
webhook_data = {
    "data": [{
        "id": 123456,
        "tid": trans_code,
        "description": f"Thanh toan {trans_code}",
        "amount": 10000,
        "when": datetime.now().isoformat()
    }]
}

print(f"🔄 Simulating Casso webhook for {trans_code}...")
print(f"Amount: 10,000đ")

# Call webhook endpoint
response = requests.post(
    "http://localhost:21120/payment/bank/webhook",
    json=webhook_data,
    headers={"Content-Type": "application/json"}
)

print(f"\n📡 Response: {response.status_code}")
print(response.json())

