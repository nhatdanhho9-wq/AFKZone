#!/usr/bin/env python3
import requests

# Check if order exists
response = requests.get("https://api.afkzone.cloud/payment/bank/status?trans_code=AFKPRO2251230003")
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

