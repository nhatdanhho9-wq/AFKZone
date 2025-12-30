#!/usr/bin/env python3
"""Test all admin endpoints"""
import requests
import json

BASE = 'https://api.afkzone.cloud'
# BASE = 'http://localhost:21120'  # For local testing

print('=' * 60)
print('Testing All Admin Endpoints')
print('=' * 60)

# 1. Login
print('\n1. Login...')
try:
    login_res = requests.post(f'{BASE}/admin/login', json={'username': 'admin', 'password': 'admin123'}, timeout=10)
    if login_res.status_code == 200:
        token = login_res.json()['access_token']
        print(f'   ✅ Login OK')
    else:
        print(f'   ❌ Login failed: {login_res.status_code}')
        exit(1)
except Exception as e:
    print(f'   ❌ Login error: {e}')
    exit(1)

headers = {'Authorization': f'Bearer {token}'}

# 2. Dashboard Stats
print('\n2. Dashboard Stats...')
try:
    res = requests.get(f'{BASE}/admin/dashboard/stats', headers=headers, timeout=10)
    if res.status_code == 200:
        data = res.json()
        print(f'   ✅ Status: {res.status_code}')
        print(f'   Devices: {data.get("total_devices", 0)}')
        print(f'   Active licenses: {data.get("total_licenses_active", 0)}')
    else:
        print(f'   ❌ Status: {res.status_code}, Error: {res.text[:200]}')
except Exception as e:
    print(f'   ❌ Error: {e}')

# 3. Products
print('\n3. Products...')
try:
    res = requests.get(f'{BASE}/products?active_only=false', timeout=10)
    if res.status_code == 200:
        data = res.json()
        print(f'   ✅ Status: {res.status_code}')
        print(f'   Products: {len(data.get("products", []))}')
    else:
        print(f'   ❌ Status: {res.status_code}')
except Exception as e:
    print(f'   ❌ Error: {e}')

# 4. Licenses
print('\n4. Licenses...')
try:
    res = requests.get(f'{BASE}/list', headers={'admin_key': 'afkzone-admin-2025'}, timeout=10)
    if res.status_code == 200:
        data = res.json()
        print(f'   ✅ Status: {res.status_code}')
        print(f'   Total: {data.get("total", 0)}')
        print(f'   Licenses: {len(data.get("licenses", []))}')
    else:
        print(f'   ❌ Status: {res.status_code}, Error: {res.text[:200]}')
except Exception as e:
    print(f'   ❌ Error: {e}')

# 5. Users/Devices
print('\n5. Users/Devices...')
try:
    res = requests.get(f'{BASE}/admin/users?limit=10', headers=headers, timeout=10)
    if res.status_code == 200:
        data = res.json()
        print(f'   ✅ Status: {res.status_code}')
        print(f'   Total: {data.get("total", 0)}')
        print(f'   Users: {len(data.get("users", []))}')
    else:
        print(f'   ❌ Status: {res.status_code}, Error: {res.text[:200]}')
except Exception as e:
    print(f'   ❌ Error: {e}')

# 6. Connections
print('\n6. Connections...')
try:
    res = requests.get(f'{BASE}/admin/connections?limit=10', headers=headers, timeout=10)
    if res.status_code == 200:
        data = res.json()
        print(f'   ✅ Status: {res.status_code}')
        print(f'   Total: {data.get("total", 0)}')
        print(f'   Connections: {len(data.get("connections", []))}')
    elif res.status_code == 404:
        print(f'   ⚠️  Status: 404 (endpoint not found or table doesn\'t exist)')
    else:
        print(f'   ❌ Status: {res.status_code}, Error: {res.text[:200]}')
except Exception as e:
    print(f'   ❌ Error: {e}')

# 7. Generate License
print('\n7. Generate License...')
try:
    res = requests.post(
        f'{BASE}/admin/licenses/generate',
        headers={**headers, 'Content-Type': 'application/json'},
        json={'tier': 'basic', 'duration_days': 30, 'max_devices': 2},
        timeout=10
    )
    if res.status_code == 200:
        data = res.json()
        print(f'   ✅ Status: {res.status_code}')
        print(f'   License key: {data.get("license_key", "N/A")}')
    else:
        print(f'   ❌ Status: {res.status_code}, Error: {res.text[:200]}')
except Exception as e:
    print(f'   ❌ Error: {e}')

print('\n' + '=' * 60)
print('Testing Complete')
print('=' * 60)

