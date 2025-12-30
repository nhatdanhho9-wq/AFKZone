#!/usr/bin/env python3
"""Add /admin endpoint to app.py"""

with open('/app/app.py', 'r') as f:
    content = f.read()

# Check if already added
if '@app.get("/admin")' in content:
    print('✅ /admin endpoint already exists')
    exit(0)

# Add import
if 'from fastapi.responses import HTMLResponse' not in content:
    content = content.replace(
        'from fastapi import',
        'from fastapi.responses import HTMLResponse\nfrom fastapi import'
    )
    print('✅ Added HTMLResponse import')

# Add endpoint after root endpoint
root_endpoint_end = content.find('}', content.find('@app.get("/")'))
if root_endpoint_end > 0:
    next_endpoint = content.find('\n@app.', root_endpoint_end)
    if next_endpoint > 0:
        endpoint_code = '''

@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard():
    """Serve admin dashboard"""
    with open("/app/admin_dashboard.html", "r", encoding="utf-8") as f:
        return f.read()

'''
        content = content[:next_endpoint] + endpoint_code + content[next_endpoint:]
        print('✅ Added /admin endpoint')
    else:
        print('❌ Could not find insertion point')
        exit(1)
else:
    print('❌ Could not find root endpoint')
    exit(1)

# Write back
with open('/app/app.py', 'w') as f:
    f.write(content)

# Verify
import ast
try:
    ast.parse(content)
    print('✅ Syntax is valid')
except SyntaxError as e:
    print(f'❌ Syntax error: {e}')
    exit(1)

