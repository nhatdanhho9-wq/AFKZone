#!/usr/bin/env python3
import requests

# Login
login = requests.post('https://api.afkzone.cloud/admin/login', json={'username':'admin','password':'admin123'})
token = login.json()['access_token']
print('Token OK')

# Test /admin/licenses
res = requests.get('https://api.afkzone.cloud/admin/licenses', headers={'Authorization': 'Bearer ' + token})
print('Status:', res.status_code)
if res.status_code == 200:
    data = res.json()
    print('Total:', data.get('total', 0))
    print('Licenses:', len(data.get('licenses', [])))
else:
    print('Error:', res.text[:200])

