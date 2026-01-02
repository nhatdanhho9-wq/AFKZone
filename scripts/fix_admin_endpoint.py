#!/usr/bin/env python3
"""Fix admin endpoint in app.py"""

# Read current app.py
with open('/app/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove broken endpoint at the end if exists
lines = content.split('\n')
new_lines = []
skip = False
for i, line in enumerate(lines):
    # Skip broken endpoint lines
    if 'from fastapi.responses import FileResponse' in line and i >= len(lines) - 15:
        skip = True
        continue
    if skip and ('@app.get' in line or 'def admin_dashboard' in line or 'FileResponse' in line or line.strip() == ''):
        if 'return {' in line or '}' in line:
            skip = False
        continue
    skip = False
    new_lines.append(line)

# Remove duplicate import if exists
if 'from fastapi.responses import HTMLResponse' not in '\n'.join(new_lines):
    new_lines.append('')
    new_lines.append('from fastapi.responses import HTMLResponse')

# Add correct endpoint at the end
new_lines.append('')
new_lines.append('@app.get("/admin", response_class=HTMLResponse)')
new_lines.append('def admin_dashboard():')
new_lines.append('    """Serve admin dashboard HTML"""')
new_lines.append('    try:')
new_lines.append('        with open("/app/admin_dashboard.html", "r", encoding="utf-8") as f:')
new_lines.append('            return f.read()')
new_lines.append('    except FileNotFoundError:')
new_lines.append('        return HTMLResponse("<h1>Admin Dashboard not found</h1>", status_code=404)')

# Write back
with open('/app/app.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print('✅ Fixed admin endpoint')

