#!/usr/bin/env python3
"""Test all admin endpoints"""
import requests
import json

BASE = 'http://localhost:21120'

# 1. Login
print('1. Testing login...')
login_res = requests.post(f'{BASE}/admin/login', json={'username': 'admin', 'password': 'admin123'})
if login_res.status_code == 200:
    token = login_res.json()['access_token']
    print(f'   ✅ Login OK, token: {token[:30]}...')
else:
    print(f'   ❌ Login failed: {login_res.status_code} - {login_res.text}')
    exit(1)

# 2. Test /list
print('\n2. Testing /list endpoint...')
list_res = requests.get(f'{BASE}/list', headers={'admin_key': 'afkzone-admin-2025'})
print(f'   Status: {list_res.status_code}')
if list_res.status_code == 200:
    data = list_res.json()
    print(f'   Total: {data.get("total", 0)}')
    print(f'   Licenses count: {len(data.get("licenses", []))}')
    if data.get('licenses') and len(data['licenses']) > 0:
        sample = data['licenses'][0]
        print(f'   Sample license keys: {list(sample.keys())}')
else:
    print(f'   ❌ Error: {list_res.text}')

# 3. Test /admin/users
print('\n3. Testing /admin/users endpoint...')
users_res = requests.get(f'{BASE}/admin/users?limit=10', headers={'Authorization': f'Bearer {token}'})
print(f'   Status: {users_res.status_code}')
if users_res.status_code == 200:
    data = users_res.json()
    print(f'   Users count: {len(data.get("users", []))}')
    if data.get('users') and len(data['users']) > 0:
        sample = data['users'][0]
        print(f'   Sample user keys: {list(sample.keys())}')
else:
    print(f'   ❌ Error: {users_res.text}')

# 4. Test /products
print('\n4. Testing /products endpoint...')
products_res = requests.get(f'{BASE}/products?active_only=false')
print(f'   Status: {products_res.status_code}')
if products_res.status_code == 200:
    data = products_res.json()
    print(f'   Products count: {len(data.get("products", []))}')
else:
    print(f'   ❌ Error: {products_res.text}')

# 5. Test /admin/dashboard/stats
print('\n5. Testing /admin/dashboard/stats...')
stats_res = requests.get(f'{BASE}/admin/dashboard/stats', headers={'Authorization': f'Bearer {token}'})
print(f'   Status: {stats_res.status_code}')
if stats_res.status_code == 200:
    data = stats_res.json()
    print(f'   Stats keys: {list(data.keys())}')
else:
    print(f'   ❌ Error: {stats_res.text}')

print('\n✅ All tests completed')

