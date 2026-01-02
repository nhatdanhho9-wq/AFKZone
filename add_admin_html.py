#!/usr/bin/env python3
"""Add /admin HTML endpoint"""

with open('/app/app.py', 'r') as f:
    content = f.read()

# Check if already exists
if '@app.get("/admin")' in content:
    print('Already exists')
    exit(0)

# Add at end of file
admin_endpoint = '''

# ==================== ADMIN DASHBOARD HTML ====================
from fastapi.responses import HTMLResponse as AdminHTML

@app.get("/admin", response_class=AdminHTML)
async def serve_admin_dashboard_html():
    """Serve admin dashboard HTML page"""
    try:
        with open('/app/admin_dashboard.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Admin Dashboard not found. Please upload admin_dashboard.html</h1>"
'''

content += admin_endpoint

with open('/app/app.py', 'w') as f:
    f.write(content)

import ast
try:
    ast.parse(content)
    print('OK - Added /admin endpoint')
except SyntaxError as e:
    print(f'Syntax error: {e}')

