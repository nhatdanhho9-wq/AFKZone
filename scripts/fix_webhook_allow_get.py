#!/usr/bin/env python3
"""Allow GET method for webhook testing"""

with open('/app/app.py', 'r') as f:
    content = f.read()

# Find webhook endpoint
old_webhook_def = '@app.post("/payment/bank/webhook")'
new_webhook_def = '''@app.get("/payment/bank/webhook")
async def bank_webhook_test():
    """Test endpoint for Casso webhook verification"""
    return {"success": True, "message": "Webhook endpoint is ready", "return_code": 1}

@app.post("/payment/bank/webhook")'''

if old_webhook_def in content and '@app.get("/payment/bank/webhook")' not in content:
    content = content.replace(old_webhook_def, new_webhook_def)
    print("✅ Added GET method for webhook testing")
else:
    print("❌ Already has GET method or POST not found")

with open('/app/app.py', 'w') as f:
    f.write(content)

import ast
try:
    ast.parse(content)
    print('✅ Syntax valid')
except SyntaxError as e:
    print(f'❌ Syntax error: {e}')

