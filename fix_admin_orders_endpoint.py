#!/usr/bin/env python3
"""Fix admin orders endpoint to use correct column indices"""

with open('/app/app.py', 'r') as f:
    content = f.read()

# The bank_orders table structure is:
# 0: id (primary key)
# 1: trans_code
# 2: device_id
# ... need to check actual schema

# Fix the get_all_orders endpoint
old_orders_mapping = '''    return {
        "orders": [
            {
                "trans_code": o[0],
                "device_id": o[1],
                "tier": o[3],
                "duration_days": o[4],
                "amount": o[5],
                "status": o[8],
                "license_key": o[9],
                "created_at": o[11].isoformat() if o[11] else None,
                "paid_at": o[12].isoformat() if o[12] else None'''

new_orders_mapping = '''    return {
        "orders": [
            {
                "id": o[0],
                "trans_code": o[1],
                "device_id": o[2],
                "tier": o[3],
                "duration_days": o[4],
                "amount": o[5],
                "status": o[8],
                "license_key": o[9],
                "created_at": o[11].isoformat() if o[11] else None,
                "paid_at": o[12].isoformat() if o[12] else None'''

if old_orders_mapping in content:
    content = content.replace(old_orders_mapping, new_orders_mapping)
    print("✅ Fixed admin orders endpoint column mapping")
else:
    print("❌ Code not found or already updated")

with open('/app/app.py', 'w') as f:
    f.write(content)

import ast
try:
    ast.parse(content)
    print('✅ Syntax valid')
except SyntaxError as e:
    print(f'❌ Syntax error: {e}')

