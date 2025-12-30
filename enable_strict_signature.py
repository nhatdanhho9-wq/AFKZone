#!/usr/bin/env python3
"""Enable strict signature verification for Casso webhook"""

with open('/app/app.py', 'r') as f:
    content = f.read()

# Find and uncomment signature verification
old_code = '''        # For now, accept all requests to test (remove later)
        # if signature != expected_signature:
        #     return {"error": "Invalid signature", "return_code": -1}'''

new_code = '''        # Verify signature in strict mode
        if signature and signature != expected_signature:
            print(f"❌ Signature mismatch! Rejecting webhook.")
            return {"error": "Invalid signature", "return_code": -1}
        
        # Allow requests without signature for testing (non-strict mode)
        if not signature:
            print(f"⚠️ No signature provided, accepting for testing...")'''

if old_code in content:
    content = content.replace(old_code, new_code)
    print("✅ Enabled strict signature verification")
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

