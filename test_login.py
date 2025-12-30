#!/usr/bin/env python3
"""Test admin login"""
import requests
import json

url = 'https://api.afkzone.cloud/admin/login'
data = {
    'username': 'admin',
    'password': 'admin123'
}

try:
    response = requests.post(url, json=data, timeout=10)
    print(f'Status Code: {response.status_code}')
    print(f'Response: {json.dumps(response.json(), indent=2)}')
except Exception as e:
    print(f'Error: {e}')

