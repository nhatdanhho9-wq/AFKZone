#!/usr/bin/env python3
import requests

# Get first order to see structure
response = requests.get("https://api.afkzone.cloud/payment/bank/status?trans_code=AFKPRO2251230006")
if response.status_code == 200:
    print("Sample order from /payment/bank/status:")
    print(response.json())

# Try to get order by ID
print("\n\nTrying direct database query...")
import sys
sys.path.insert(0, '/home/automation')

# We need to check the actual column order in bank_orders table
print("Need to check database schema on server...")

